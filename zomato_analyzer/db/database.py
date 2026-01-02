"""Database initialization and operations."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from zomato_analyzer.models.order import Order


class OrderDatabase:
    """SQLite database for storing Zomato orders."""
    
    def __init__(self, db_path: str = "zomato_orders.db"):
        """Initialize database connection."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = None
        self.init_db()
    
    def init_db(self):
        """Create database and tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create orders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT UNIQUE NOT NULL,
                    order_date TEXT NOT NULL,
                    restaurant_name TEXT NOT NULL,
                    amount REAL NOT NULL,
                    delivery_fee REAL DEFAULT 0,
                    discount REAL DEFAULT 0,
                    total_amount REAL NOT NULL,
                    status TEXT DEFAULT 'completed',
                    payment_method TEXT,
                    delivery_location TEXT,
                    order_items TEXT,
                    raw_email_body TEXT,
                    email_date TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_order_date 
                ON orders(order_date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_restaurant_name 
                ON orders(restaurant_name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_order_id 
                ON orders(order_id)
            """)
            
            conn.commit()
    
    def get_connection(self):
        """Get database connection."""
        if self.connection is None:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def insert_order(self, order: Order, upsert: bool = True) -> bool:
        """
        Insert or update an order (idempotent).
        
        Args:
            order: Order object to insert
            upsert: If True, update existing order; if False, skip existing
            
        Returns:
            True if inserted/updated, False if already exists and upsert=False
        """
        now = datetime.now(timezone.utc).isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if order exists
            cursor.execute(
                "SELECT id FROM orders WHERE order_id = ?",
                (order.order_id,)
            )
            existing = cursor.fetchone()
            
            if existing:
                if not upsert:
                    return False
                
                # Update existing order
                cursor.execute("""
                    UPDATE orders SET
                        order_date = ?,
                        restaurant_name = ?,
                        amount = ?,
                        delivery_fee = ?,
                        discount = ?,
                        total_amount = ?,
                        status = ?,
                        payment_method = ?,
                        delivery_location = ?,
                        order_items = ?,
                        raw_email_body = ?,
                        email_date = ?,
                        updated_at = ?
                    WHERE order_id = ?
                """, (
                    order.order_date.isoformat(),
                    order.restaurant_name,
                    order.amount,
                    order.delivery_fee,
                    order.discount,
                    order.total_amount,
                    order.status,
                    order.payment_method,
                    order.delivery_location,
                    order.order_items,
                    order.raw_email_body,
                    order.email_date.isoformat() if order.email_date else None,
                    now,
                    order.order_id
                ))
            else:
                # Insert new order
                cursor.execute("""
                    INSERT INTO orders (
                        order_id, order_date, restaurant_name, amount,
                        delivery_fee, discount, total_amount, status,
                        payment_method, delivery_location, order_items,
                        raw_email_body, email_date, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    order.order_id,
                    order.order_date.isoformat(),
                    order.restaurant_name,
                    order.amount,
                    order.delivery_fee,
                    order.discount,
                    order.total_amount,
                    order.status,
                    order.payment_method,
                    order.delivery_location,
                    order.order_items,
                    order.raw_email_body,
                    order.email_date.isoformat() if order.email_date else None,
                    now,
                    now
                ))
            
            conn.commit()
            return True
    
    def get_all_orders(self) -> List[Order]:
        """Get all orders from database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orders ORDER BY order_date DESC")
            rows = cursor.fetchall()
            
            return [self._row_to_order(row) for row in rows]
    
    def get_orders_by_restaurant(self, restaurant_name: str) -> List[Order]:
        """Get all orders for a specific restaurant."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM orders WHERE restaurant_name = ? ORDER BY order_date DESC",
                (restaurant_name,)
            )
            rows = cursor.fetchall()
            
            return [self._row_to_order(row) for row in rows]
    
    def get_orders_by_year(self, year: int) -> List[Order]:
        """Get all orders for a specific year."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM orders 
                WHERE strftime('%Y', order_date) = ?
                ORDER BY order_date DESC
            """, (str(year),))
            rows = cursor.fetchall()
            
            return [self._row_to_order(row) for row in rows]
    
    def get_orders_by_month(self, year: int, month: int) -> List[Order]:
        """Get all orders for a specific month."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM orders 
                WHERE strftime('%Y-%m', order_date) = ?
                ORDER BY order_date DESC
            """, (f"{year:04d}-{month:02d}",))
            rows = cursor.fetchall()
            
            return [self._row_to_order(row) for row in rows]
    
    def get_order_count(self) -> int:
        """Get total number of orders."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM orders")
            return cursor.fetchone()[0]
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()
    
    @staticmethod
    def _row_to_order(row: sqlite3.Row) -> Order:
        """Convert database row to Order object."""
        return Order(
            order_id=row['order_id'],
            order_date=datetime.fromisoformat(row['order_date']),
            restaurant_name=row['restaurant_name'],
            amount=row['amount'],
            delivery_fee=row['delivery_fee'],
            discount=row['discount'],
            total_amount=row['total_amount'],
            status=row['status'],
            payment_method=row['payment_method'],
            delivery_location=row['delivery_location'],
            order_items=row['order_items'],
            raw_email_body=row['raw_email_body'],
            email_date=datetime.fromisoformat(row['email_date']) if row['email_date'] else None
        )
