"""Strict typed views and valid generated inputs; negative tests send raw dicts."""

from pydantic import BaseModel, ConfigDict, Field


class Product(BaseModel):
    """Only fields consumed by our tests; the service may add other fields."""

    model_config = ConfigDict(strict=True, extra="ignore", frozen=True, hide_input_in_errors=True)

    id: int = Field(gt=0)
    title: str = Field(min_length=1)
    price: float = Field(ge=0, allow_inf_nan=False)
    category: str = Field(min_length=1)
    stock: int = Field(ge=0)
    rating: float = Field(ge=0, le=5, allow_inf_nan=False)


class CartItem(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class CartCreate(BaseModel):
    """Our payload policy is stricter than DummyJSON's permissive demo API."""

    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    user_id: int = Field(alias="userId", gt=0)
    products: list[CartItem] = Field(min_length=1)
