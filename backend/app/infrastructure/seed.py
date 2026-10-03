from app.infrastructure.db import SessionLocal, init_db
from app.infrastructure.models import ProductModel

SEED_PRODUCTS = [
    {"sku": "COFFEE-001", "name": "Cold Brew Coffee", "price_cents": 599, "quantity": 120},
    {"sku": "MUG-001", "name": "Ceramic Travel Mug", "price_cents": 1899, "quantity": 45},
    {"sku": "BEANS-001", "name": "Single-Origin Coffee Beans", "price_cents": 1499, "quantity": 80},
]


def seed() -> None:
    init_db()
    db = SessionLocal()
    try:
        if db.query(ProductModel).count():
            return
        for item in SEED_PRODUCTS:
            db.add(
                ProductModel(
                    sku=item["sku"],
                    name=item["name"],
                    price_cents=item["price_cents"],
                    available_quantity=item["quantity"],
                )
            )
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
