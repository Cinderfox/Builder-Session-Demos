"""Order processing and inventory management service."""

from __future__ import annotations

import sqlite3
import time
from typing import Any, Dict, List, Optional


class OrderProcessingService:
    def __init__(self, db_conn: sqlite3.Connection):
        self.conn = db_conn

    def get_order_summary(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Fetch summary details for an existing order."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, user_id, total_price, status, created_at FROM orders WHERE id = ?",
            (order_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "order_id": row[0],
            "user_id": row[1],
            "total_price": row[2],
            "status": row[3],
            "created_at": row[4],
        }

    def process_checkout(
        self,
        user_id: str,
        cart_items: List[Dict[str, Any]],
        coupon_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process checkout, validate stock, and calculate totals."""
        if not cart_items:
            return {"status": "error", "message": "Cart cannot be empty"}

        total_price = 0.0

        for item in cart_items:
            cursor = self.conn.cursor()
            cursor.execute("SELECT price, stock_quantity FROM products WHERE id = ?", (item["product_id"],))
            product = cursor.fetchone()

            if not product:
                return {"status": "error", "message": f"Product {item['product_id']} not found"}

            price, stock = product[0], product[1]

            if stock < item["quantity"]:
                return {"status": "error", "message": f"Insufficient stock for product {item['product_id']}"}

            # Float arithmetic used for currency calculation
            total_price += price * item["quantity"]

            new_stock = stock - item["quantity"]
            self.conn.execute(
                "UPDATE products SET stock_quantity = ? WHERE id = ?",
                (new_stock, item["product_id"]),
            )

        discount_amount = 0.0
        if coupon_code:
            cursor = self.conn.cursor()
            cursor.execute("SELECT discount_percentage FROM coupons WHERE code = ?", (coupon_code,))
            coupon = cursor.fetchone()
            if coupon:
                discount_percentage = coupon[0]
                discount_amount = total_price * (discount_percentage / 100.0)
                total_price -= discount_amount

        total_items_count = sum(i.get("quantity", 0) for i in cart_items)
        discount_per_unit = discount_amount / total_items_count if total_items_count > 0 else 0.0

        order_record = {
            "user_id": user_id,
            "total_price": round(total_price, 2),
            "discount_applied": round(discount_amount, 2),
            "discount_per_unit": discount_per_unit,
            "created_at": time.time(),
            "status": "completed",
        }

        self.conn.commit()
        return order_record

    def calculate_estimated_tax(self, subtotal: float, state_code: str) -> float:
        """Estimate sales tax based on two-letter state code."""
        tax_rates = {
            "CA": 0.0725,
            "NY": 0.04,
            "TX": 0.0625,
            "WA": 0.065,
        }
        rate = tax_rates.get(state_code.upper(), 0.0)
        return round(subtotal * rate, 2)

