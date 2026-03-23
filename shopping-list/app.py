import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from models import get_db, init_db, generate_share_token
from delivery_providers import mock as delivery

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")


@app.before_request
def ensure_db():
    init_db()


# --- Views ---


@app.route("/")
def index():
    db = get_db()
    lists = db.execute(
        "SELECT * FROM shopping_lists ORDER BY created_at DESC"
    ).fetchall()
    db.close()
    return render_template("index.html", lists=lists)


@app.route("/list/new", methods=["POST"])
def create_list():
    name = request.form.get("name", "").strip()
    if not name:
        name = "Minha Lista"
    db = get_db()
    token = generate_share_token()
    db.execute(
        "INSERT INTO shopping_lists (name, share_token) VALUES (?, ?)",
        (name, token),
    )
    db.commit()
    list_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()
    return redirect(url_for("edit_list", list_id=list_id))


@app.route("/list/<int:list_id>")
def edit_list(list_id):
    db = get_db()
    shopping_list = db.execute(
        "SELECT * FROM shopping_lists WHERE id = ?", (list_id,)
    ).fetchone()
    if not shopping_list:
        flash("Lista não encontrada", "error")
        return redirect(url_for("index"))

    items = db.execute(
        """SELECT i.*, c.name as category_name
           FROM items i
           LEFT JOIN categories c ON i.category_id = c.id
           WHERE i.list_id = ?
           ORDER BY c.name, i.name""",
        (list_id,),
    ).fetchall()
    categories = db.execute(
        "SELECT * FROM categories ORDER BY name"
    ).fetchall()
    db.close()
    return render_template(
        "list.html", list=shopping_list, items=items, categories=categories
    )


# --- Shared list (read-only by default, editable via token) ---


@app.route("/s/<token>")
def shared_list(token):
    db = get_db()
    shopping_list = db.execute(
        "SELECT * FROM shopping_lists WHERE share_token = ?", (token,)
    ).fetchone()
    if not shopping_list:
        flash("Lista não encontrada", "error")
        return redirect(url_for("index"))

    items = db.execute(
        """SELECT i.*, c.name as category_name
           FROM items i
           LEFT JOIN categories c ON i.category_id = c.id
           WHERE i.list_id = ?
           ORDER BY c.name, i.name""",
        (shopping_list["id"],),
    ).fetchall()
    categories = db.execute(
        "SELECT * FROM categories ORDER BY name"
    ).fetchall()
    db.close()
    return render_template(
        "list.html",
        list=shopping_list,
        items=items,
        categories=categories,
        shared=True,
    )


@app.route("/list/<int:list_id>/share", methods=["POST"])
def generate_share_link(list_id):
    db = get_db()
    row = db.execute(
        "SELECT share_token FROM shopping_lists WHERE id = ?", (list_id,)
    ).fetchone()
    if not row:
        db.close()
        return jsonify({"error": "Lista não encontrada"}), 404
    token = row["share_token"]
    if not token:
        token = generate_share_token()
        db.execute(
            "UPDATE shopping_lists SET share_token = ? WHERE id = ?",
            (token, list_id),
        )
        db.commit()
    db.close()
    share_url = url_for("shared_list", token=token, _external=True)
    return jsonify({"url": share_url, "token": token})


# --- Item CRUD ---


@app.route("/list/<int:list_id>/item", methods=["POST"])
def add_item(list_id):
    name = request.form.get("name", "").strip()
    if not name:
        return redirect(url_for("edit_list", list_id=list_id))

    quantity = float(request.form.get("quantity", 1))
    unit = request.form.get("unit", "un")
    category_id = request.form.get("category_id") or None
    estimated_price = request.form.get("estimated_price") or None
    if estimated_price:
        estimated_price = float(estimated_price)

    db = get_db()
    db.execute(
        """INSERT INTO items (name, quantity, unit, category_id, estimated_price, list_id)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (name, quantity, unit, category_id, estimated_price, list_id),
    )
    db.commit()
    db.close()
    return redirect(url_for("edit_list", list_id=list_id))


@app.route("/item/<int:item_id>/update", methods=["POST"])
def update_item(item_id):
    db = get_db()
    item = db.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if not item:
        db.close()
        return jsonify({"error": "Item não encontrado"}), 404

    data = request.get_json() if request.is_json else request.form
    name = data.get("name", item["name"])
    quantity = float(data.get("quantity", item["quantity"]))
    unit = data.get("unit", item["unit"])
    category_id = data.get("category_id") or item["category_id"]
    estimated_price = data.get("estimated_price")
    if estimated_price is not None and estimated_price != "":
        estimated_price = float(estimated_price)
    else:
        estimated_price = item["estimated_price"]

    db.execute(
        """UPDATE items SET name=?, quantity=?, unit=?, category_id=?, estimated_price=?
           WHERE id=?""",
        (name, quantity, unit, category_id, estimated_price, item_id),
    )
    db.commit()
    db.close()

    if request.is_json:
        return jsonify({"ok": True})
    return redirect(url_for("edit_list", list_id=item["list_id"]))


@app.route("/item/<int:item_id>/quantity", methods=["POST"])
def update_quantity(item_id):
    """Inline quantity adjustment (+/-)."""
    db = get_db()
    item = db.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if not item:
        db.close()
        return jsonify({"error": "Item não encontrado"}), 404

    data = request.get_json() or {}
    delta = float(data.get("delta", 0))
    new_qty = max(0.1, item["quantity"] + delta)

    db.execute("UPDATE items SET quantity = ? WHERE id = ?", (new_qty, item_id))
    db.commit()
    db.close()
    return jsonify({"ok": True, "quantity": new_qty})


@app.route("/item/<int:item_id>/toggle", methods=["POST"])
def toggle_item(item_id):
    db = get_db()
    db.execute(
        "UPDATE items SET checked = NOT checked WHERE id = ?", (item_id,)
    )
    db.commit()
    item = db.execute(
        "SELECT list_id FROM items WHERE id = ?", (item_id,)
    ).fetchone()
    db.close()
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": True})
    return redirect(url_for("edit_list", list_id=item["list_id"]))


@app.route("/item/<int:item_id>/delete", methods=["POST"])
def delete_item(item_id):
    db = get_db()
    item = db.execute(
        "SELECT list_id FROM items WHERE id = ?", (item_id,)
    ).fetchone()
    db.execute("DELETE FROM items WHERE id = ?", (item_id,))
    db.commit()
    db.close()
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": True})
    return redirect(url_for("edit_list", list_id=item["list_id"]))


@app.route("/list/<int:list_id>/delete", methods=["POST"])
def delete_list(list_id):
    db = get_db()
    db.execute("DELETE FROM shopping_lists WHERE id = ?", (list_id,))
    db.commit()
    db.close()
    flash("Lista excluída", "success")
    return redirect(url_for("index"))


# --- Delivery / Order Flow ---


@app.route("/list/<int:list_id>/order")
def review_order(list_id):
    db = get_db()
    shopping_list = db.execute(
        "SELECT * FROM shopping_lists WHERE id = ?", (list_id,)
    ).fetchone()
    items = db.execute(
        """SELECT i.*, c.name as category_name
           FROM items i
           LEFT JOIN categories c ON i.category_id = c.id
           WHERE i.list_id = ? AND i.checked = 0
           ORDER BY c.name, i.name""",
        (list_id,),
    ).fetchall()
    db.close()

    if not items:
        flash("Adicione itens à lista antes de pedir.", "warning")
        return redirect(url_for("edit_list", list_id=list_id))

    cart_items = [{"name": item["name"], "quantity": item["quantity"]} for item in items]
    cart = delivery.create_cart(cart_items)

    return render_template(
        "review_order.html", list=shopping_list, cart=cart, items=items
    )


@app.route("/list/<int:list_id>/confirm", methods=["POST"])
def confirm_order(list_id):
    cart_id = request.form.get("cart_id")
    if not cart_id:
        flash("Carrinho inválido", "error")
        return redirect(url_for("edit_list", list_id=list_id))

    order = delivery.place_order(cart_id)

    if "error" in order:
        flash(order["error"], "error")
        return redirect(url_for("edit_list", list_id=list_id))

    db = get_db()
    db.execute(
        """UPDATE shopping_lists
           SET status = 'ordered', ordered_at = datetime('now'),
               delivery_provider = 'MockMarket',
               delivery_order_id = ?
           WHERE id = ?""",
        (order["order_id"], list_id),
    )
    db.execute(
        """INSERT INTO order_history (list_id, status, details)
           VALUES (?, 'confirmed', ?)""",
        (list_id, f"Pedido {order['order_id']} confirmado. Entrega estimada: {order['estimated_delivery']}"),
    )
    db.commit()
    db.close()

    flash(f"Pedido {order['order_id']} confirmado! Entrega estimada: {order['estimated_delivery']}", "success")
    return redirect(url_for("order_status", list_id=list_id))


@app.route("/list/<int:list_id>/status")
def order_status(list_id):
    db = get_db()
    shopping_list = db.execute(
        "SELECT * FROM shopping_lists WHERE id = ?", (list_id,)
    ).fetchone()
    history = db.execute(
        "SELECT * FROM order_history WHERE list_id = ? ORDER BY created_at DESC",
        (list_id,),
    ).fetchall()
    db.close()

    order = None
    if shopping_list["delivery_order_id"]:
        order = delivery.get_order_status(shopping_list["delivery_order_id"])

    return render_template(
        "order_status.html", list=shopping_list, order=order, history=history
    )


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1", host="0.0.0.0", port=port)
