from typing import Any


def cart_payload(user_id: int, product_id: int, *, quantity: int = 2) -> dict[str, Any]:
    """Return a fresh payload each time; never mutate shared test data."""
    if user_id <= 0 or product_id <= 0 or quantity <= 0:
        raise ValueError("User ID, product ID, and quantity must be positive")
    return {"userId": user_id, "products": [{"id": product_id, "quantity": quantity}]}
