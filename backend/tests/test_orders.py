import pytest

from app.application.services import CatalogService, OrderService
from app.domain.errors import InsufficientInventory, OrderAlreadyCancelled
from app.infrastructure.models import ProductModel


def create_catalog(db):
    catalog = CatalogService()
    coffee = catalog.create_product(db, "COFFEE-001", "Cold Brew", 599, 2)
    mug = catalog.create_product(db, "MUG-001", "Travel Mug", 1899, 10)
    return coffee, mug


def test_order_reserves_inventory_and_is_idempotent(db):
    create_catalog(db)
    service = OrderService()

    first = service.create_order(
        db,
        "buyer@example.com",
        [{"sku": "COFFEE-001", "quantity": 2}],
        "checkout-1234",
    )
    second = service.create_order(
        db,
        "buyer@example.com",
        [{"sku": "COFFEE-001", "quantity": 2}],
        "checkout-1234",
    )

    assert first.id == second.id
    assert first.total_cents == 1198
    inventory = db.query(ProductModel).filter_by(sku="COFFEE-001").one()
    assert inventory.available_quantity == 0
    assert inventory.reserved_quantity == 2


def test_order_fails_without_enough_inventory(db):
    create_catalog(db)

    with pytest.raises(InsufficientInventory):
        OrderService().create_order(
            db,
            "buyer@example.com",
            [{"sku": "COFFEE-001", "quantity": 3}],
            "checkout-5678",
        )


def test_cancel_releases_inventory(db):
    create_catalog(db)
    service = OrderService()
    order = service.create_order(
        db,
        "buyer@example.com",
        [{"sku": "COFFEE-001", "quantity": 1}],
        "checkout-9999",
    )

    cancelled = service.cancel_order(db, order.id)
    assert cancelled.status == "cancelled"
    inventory = db.query(ProductModel).filter_by(sku="COFFEE-001").one()
    assert inventory.available_quantity == 2
    assert inventory.reserved_quantity == 0

    with pytest.raises(OrderAlreadyCancelled):
        service.cancel_order(db, order.id)
