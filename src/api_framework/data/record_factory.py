from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ProductRecordData(BaseModel):
    """Our valid generator policy for the starter Products collection."""

    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)
    name: str = Field(min_length=1)
    price: float = Field(ge=0, allow_inf_nan=False)
    category: str = Field(min_length=1)
    in_stock: bool


def product_record_data(*, price: float = 9.99, in_stock: bool = True) -> dict[str, Any]:
    return ProductRecordData(
        name=f"QA-{uuid4().hex}", price=price, category="Portfolio", in_stock=in_stock
    ).model_dump()
