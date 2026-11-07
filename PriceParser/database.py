"""SQLite schema and connections for the local price tracker."""
import os
import sqlite3
from contextlib import closing
from pathlib import Path

DATABASE_PATH = Path(os.environ.get('PRICEPARSER_DB', Path(__file__).with_name('prices.db')))


def get_connection():
    return sqlite3.connect(DATABASE_PATH)


def init_database():
    with closing(get_connection()) as conn, conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                price REAL NOT NULL,
                shop TEXT DEFAULT 'vodoparad.ru',
                parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            );
            CREATE TABLE IF NOT EXISTS parsing_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_url TEXT,
                status TEXT,
                price REAL,
                shop_name TEXT,
                message TEXT,
                parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)


if __name__ == '__main__':
    init_database()
    print('База данных готова')
