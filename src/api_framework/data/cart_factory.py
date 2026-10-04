from typing import Any

from api_framework.contracts.models import CartCreate, CartItem


def cart_payload(user_id: int, product_id: int, *, quantity: int = 2) -> dict[str, Any]:
    """Return a fresh payload each time; never mutate shared test data."""
    model = CartCreate(userId=user_id, products=[CartItem(id=product_id, quantity=quantity)])
    return model.model_dump(by_alias=True)
