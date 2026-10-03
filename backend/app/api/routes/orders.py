from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from app.api.deps import enforce_rate_limit
from app.api.schemas import OrderCreate, OrderResponse
from app.application.services import OrderService
from app.infrastructure.db import get_db
from app.infrastructure.repositories import get_order

router = APIRouter(prefix="/orders", tags=["orders"], dependencies=[Depends(enforce_rate_limit)])
service = OrderService()


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    idempotency_key: str = Header(min_length=8, max_length=160, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    return service.create_order(
        db,
        customer_email=payload.customer_email,
        items=[item.model_dump() for item in payload.items],
        idempotency_key=idempotency_key,
    )


@router.get("/{order_id}", response_model=OrderResponse)
def get_order_by_id(order_id: str, db: Session = Depends(get_db)):
    return get_order(db, order_id)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(order_id: str, db: Session = Depends(get_db)):
    return service.cancel_order(db, order_id)
