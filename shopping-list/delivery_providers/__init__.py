"""
Delivery provider integrations.

Each provider implements:
    - search_products(query: str) -> list[dict]
    - create_cart(items: list[dict]) -> dict
    - review_cart(cart_id: str) -> dict
    - place_order(cart_id: str) -> dict
    - get_order_status(order_id: str) -> dict
"""
