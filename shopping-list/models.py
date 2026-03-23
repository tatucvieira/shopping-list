import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "shopping.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity REAL NOT NULL DEFAULT 1,
            unit TEXT DEFAULT 'un',
            category_id INTEGER,
            estimated_price REAL,
            checked INTEGER NOT NULL DEFAULT 0,
            list_id INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (category_id) REFERENCES categories(id),
            FOREIGN KEY (list_id) REFERENCES shopping_lists(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS shopping_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            ordered_at TEXT,
            delivery_provider TEXT,
            delivery_order_id TEXT
        );

        CREATE TABLE IF NOT EXISTS order_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            details TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (list_id) REFERENCES shopping_lists(id)
        );
    """)

    default_categories = [
        "Frutas e Verduras", "Carnes e Frios", "Laticínios",
        "Padaria", "Bebidas", "Limpeza", "Higiene",
        "Mercearia", "Congelados", "Outros"
    ]
    for cat in default_categories:
        conn.execute(
            "INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,)
        )
    conn.commit()
    conn.close()
