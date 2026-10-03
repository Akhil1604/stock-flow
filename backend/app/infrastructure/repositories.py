from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.errors import OrderNotFound, ProductNotFound
from app.infrastructure.models import (
    OrderModel,
    ProductModel,
    ReservationModel,
)


def get_product(db: Session, product_id: str) -> ProductModel:
    product = db.get(ProductModel, product_id)
    if not product:
        raise ProductNotFound(f"Product {product_id} was not found")
    return product


def get_product_by_sku(db: Session, sku: str) -> ProductModel:
    product = db.scalar(select(ProductModel).where(ProductModel.sku == sku))
    if not product:
        raise ProductNotFound(f"Product with SKU {sku} was not found")
    return product


def get_order(db: Session, order_id: str) -> OrderModel:
    order = db.get(OrderModel, order_id)
    if not order:
        raise OrderNotFound(f"Order {order_id} was not found")
    return order


def get_order_by_idempotency_key(db: Session, key: str) -> OrderModel | None:
    return db.scalar(select(OrderModel).where(OrderModel.idempotency_key == key))


def list_active_reservations_for_order(db: Session, order_id: str) -> list[ReservationModel]:
    return list(
        db.scalars(
            select(ReservationModel).where(
                ReservationModel.order_id == order_id,
                ReservationModel.status == "active",
            )
        )
    )
