"""
Mock delivery provider for development and testing.
Replace with real provider (e.g., iFood, Rappi, Mercado Livre) integrations.
"""

import uuid
from datetime import datetime, timedelta

# Simulated product catalog
MOCK_CATALOG = {
    "arroz": {"name": "Arroz Tipo 1 5kg", "price": 28.90, "available": True},
    "feijão": {"name": "Feijão Carioca 1kg", "price": 8.50, "available": True},
    "leite": {"name": "Leite Integral 1L", "price": 6.20, "available": True},
    "pão": {"name": "Pão Francês (10un)", "price": 7.00, "available": True},
    "banana": {"name": "Banana Prata 1kg", "price": 5.90, "available": True},
    "frango": {"name": "Peito de Frango 1kg", "price": 18.90, "available": True},
    "tomate": {"name": "Tomate Italiano 1kg", "price": 9.50, "available": True},
    "cebola": {"name": "Cebola 1kg", "price": 5.50, "available": True},
    "alho": {"name": "Alho 200g", "price": 4.90, "available": True},
    "óleo": {"name": "Óleo de Soja 900ml", "price": 7.80, "available": True},
    "açúcar": {"name": "Açúcar Refinado 1kg", "price": 5.40, "available": True},
    "café": {"name": "Café Torrado 500g", "price": 16.90, "available": True},
    "macarrão": {"name": "Macarrão Espaguete 500g", "price": 4.50, "available": True},
    "sabão": {"name": "Sabão em Pó 1kg", "price": 12.90, "available": True},
    "papel higiênico": {"name": "Papel Higiênico 12 rolos", "price": 18.50, "available": True},
}

_carts = {}
_orders = {}


def search_products(query):
    """Search for products matching the query."""
    query_lower = query.lower()
    results = []
    for key, product in MOCK_CATALOG.items():
        if query_lower in key or query_lower in product["name"].lower():
            results.append({
                "id": key,
                "name": product["name"],
                "price": product["price"],
                "available": product["available"],
            })
    # If no exact match, return a generic result
    if not results:
        results.append({
            "id": query_lower,
            "name": query.title(),
            "price": round(5.0 + hash(query) % 30, 2),
            "available": True,
        })
    return results


def create_cart(items):
    """Create a cart with the given items. Returns cart summary for review."""
    cart_id = str(uuid.uuid4())[:8]
    cart_items = []
    total = 0.0

    for item in items:
        products = search_products(item["name"])
        product = products[0]
        subtotal = product["price"] * item.get("quantity", 1)
        cart_items.append({
            "product_id": product["id"],
            "name": product["name"],
            "quantity": item.get("quantity", 1),
            "unit_price": product["price"],
            "subtotal": round(subtotal, 2),
            "available": product["available"],
        })
        total += subtotal

    delivery_fee = 9.90
    cart = {
        "cart_id": cart_id,
        "items": cart_items,
        "subtotal": round(total, 2),
        "delivery_fee": delivery_fee,
        "total": round(total + delivery_fee, 2),
        "estimated_delivery": (datetime.now() + timedelta(hours=2)).strftime(
            "%d/%m/%Y %H:%M"
        ),
        "provider": "MockMarket",
    }
    _carts[cart_id] = cart
    return cart


def review_cart(cart_id):
    """Get cart details for review before placing order."""
    return _carts.get(cart_id)


def place_order(cart_id):
    """Confirm and place the order."""
    cart = _carts.get(cart_id)
    if not cart:
        return {"error": "Carrinho não encontrado"}

    order_id = f"ORD-{str(uuid.uuid4())[:6].upper()}"
    order = {
        "order_id": order_id,
        "cart": cart,
        "status": "confirmed",
        "placed_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "estimated_delivery": cart["estimated_delivery"],
    }
    _orders[order_id] = order
    del _carts[cart_id]
    return order


def get_order_status(order_id):
    """Check the status of an order."""
    order = _orders.get(order_id)
    if not order:
        return {"error": "Pedido não encontrado"}
    return order
