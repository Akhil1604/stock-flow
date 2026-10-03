from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.domain.errors import InsufficientInventory, InvalidOrder, OrderAlreadyCancelled
from app.domain.order import OrderStatus, validate_customer_email
from app.infrastructure.models import (
    OrderItemModel,
    OrderModel,
    OutboxEventModel,
    ProductModel,
    ReservationModel,
)
from app.infrastructure.observability import ORDER_COUNT
from app.infrastructure.repositories import (
    get_order,
    get_order_by_idempotency_key,
    get_product_by_sku,
    list_active_reservations_for_order,
)


def _lock_product(db: Session, product_id: str) -> ProductModel:
    # FOR UPDATE is honored by PostgreSQL and ignored by SQLite, which is useful for unit tests.
    return db.scalar(select(ProductModel).where(ProductModel.id == product_id).with_for_update())


class OrderService:
    def create_order(
        self,
        db: Session,
        customer_email: str,
        items: list[dict],
        idempotency_key: str,
    ) -> OrderModel:
        existing = get_order_by_idempotency_key(db, idempotency_key)
        if existing:
            return existing
        if not items:
            raise InvalidOrder("At least one item is required")
        validate_customer_email(customer_email)

        normalized: dict[str, int] = {}
        for item in items:
            sku = str(item["sku"]).strip()
            quantity = int(item["quantity"])
            if not sku or quantity < 1 or quantity > 100:
                raise InvalidOrder("Each item requires a SKU and quantity between 1 and 100")
            normalized[sku] = normalized.get(sku, 0) + quantity

        order = OrderModel(
            id=str(uuid4()),
            customer_email=customer_email,
            status=OrderStatus.CONFIRMED,
            total_cents=0,
            idempotency_key=idempotency_key,
        )
        db.add(order)
        db.flush()

        total_cents = 0
        # A deterministic lock order prevents deadlocks when two multi-item
        # orders contain the same products in different request orders.
        for sku in sorted(normalized):
            quantity = normalized[sku]
            product = get_product_by_sku(db, sku)
            locked = _lock_product(db, product.id)
            if locked.available_quantity < quantity:
                raise InsufficientInventory(
                    f"Only {locked.available_quantity} units remain for {locked.sku}"
                )
            locked.available_quantity -= quantity
            locked.reserved_quantity += quantity
            locked.version += 1
            total_cents += locked.price_cents * quantity
            order.items.append(
                OrderItemModel(
                    product_id=locked.id,
                    sku=locked.sku,
                    product_name=locked.name,
                    quantity=quantity,
                    unit_price_cents=locked.price_cents,
                )
            )
            db.add(
                ReservationModel(
                    order_id=order.id,
                    product_id=locked.id,
                    quantity=quantity,
                    status="active",
                    expires_at=datetime.now(UTC)
                    + timedelta(minutes=get_settings().reservation_ttl_minutes),
                )
            )

        order.total_cents = total_cents
        db.add(
            OutboxEventModel(
                event_type="order.confirmed",
                aggregate_id=order.id,
                payload={"order_id": order.id, "total_cents": total_cents},
            )
        )
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            existing = get_order_by_idempotency_key(db, idempotency_key)
            if existing:
                return existing
            raise
        db.refresh(order)
        ORDER_COUNT.labels(OrderStatus.CONFIRMED).inc()
        return order

    def cancel_order(self, db: Session, order_id: str) -> OrderModel:
        order = get_order(db, order_id)
        if order.status == OrderStatus.CANCELLED:
            raise OrderAlreadyCancelled(f"Order {order_id} is already cancelled")
        reservations = list_active_reservations_for_order(db, order_id)
        for reservation in reservations:
            product = _lock_product(db, reservation.product_id)
            product.available_quantity += reservation.quantity
            product.reserved_quantity -= reservation.quantity
            product.version += 1
            reservation.status = "released"
        order.status = OrderStatus.CANCELLED
        db.add(
            OutboxEventModel(
                event_type="order.cancelled",
                aggregate_id=order.id,
                payload={"order_id": order.id},
            )
        )
        db.commit()
        db.refresh(order)
        ORDER_COUNT.labels(OrderStatus.CANCELLED).inc()
        return order


class CatalogService:
    def list_products(self, db: Session) -> list[ProductModel]:
        return list(db.scalars(select(ProductModel).order_by(ProductModel.name)))

    def create_product(
        self, db: Session, sku: str, name: str, price_cents: int, quantity: int
    ) -> ProductModel:
        if price_cents < 1 or quantity < 0:
            raise InvalidOrder("price_cents must be positive and quantity cannot be negative")
        product = ProductModel(
            sku=sku.strip(), name=name.strip(), price_cents=price_cents, available_quantity=quantity
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product
