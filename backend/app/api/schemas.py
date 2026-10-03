from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=80, examples=["COFFEE-001"])
    name: str = Field(min_length=1, max_length=180, examples=["Cold Brew Coffee"])
    price_cents: int = Field(gt=0, examples=[599])
    quantity: int = Field(ge=0, le=1_000_000, examples=[100])


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    sku: str
    name: str
    price_cents: int
    available_quantity: int
    reserved_quantity: int
    version: int


class OrderItemRequest(BaseModel):
    sku: str = Field(min_length=1, max_length=80)
    quantity: int = Field(gt=0, le=100)


class OrderCreate(BaseModel):
    customer_email: str = Field(min_length=3, max_length=320)
    items: list[OrderItemRequest] = Field(min_length=1, max_length=50)


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sku: str
    product_name: str
    quantity: int
    unit_price_cents: int


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_email: str
    status: str
    total_cents: int
    created_at: datetime | None
    items: list[OrderItemResponse]
