from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import enforce_rate_limit, require_admin_key
from app.api.schemas import ProductCreate, ProductResponse
from app.application.services import CatalogService
from app.infrastructure.db import get_db

router = APIRouter(prefix="/products", tags=["catalog"], dependencies=[Depends(enforce_rate_limit)])
service = CatalogService()


@router.get("", response_model=list[ProductResponse])
def list_products(db: Session = Depends(get_db)):
    return service.list_products(db)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key),
):
    return service.create_product(db, **payload.model_dump())
