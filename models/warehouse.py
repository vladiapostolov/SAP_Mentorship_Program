from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

from models.item import Item


@dataclass
class Warehouse:
    """
    Maps to `warehouses` table.

    Fields:
      - items (handled via DB, not stored in object)
      - timestamp_created

    Methods:
      - quantity_per_item
      - return_item
      - add_item
      - remove_item
      - list_items
    """
    id: int
    name: str
    timestamp_created: Optional[datetime] = None

    # ---------- Loading ----------
    @staticmethod
    def load_by_id(warehouse_id: int) -> Optional["Warehouse"]:
        from db.connection import db_cursor
        with db_cursor() as (_, cur):
            cur.execute(
                "SELECT id, name, timestamp_created FROM warehouses WHERE id=%s",
                (warehouse_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return Warehouse(id=row["id"], name=row["name"], timestamp_created=row["timestamp_created"])

    # ---------- Item queries ----------
    def list_items(self) -> list[Item]:
        from db.connection import db_cursor
        with db_cursor() as (_, cur):
            # uses base table (safe). If you prefer your view: SELECT * FROM vw_inventory WHERE warehouse_id=%s
            cur.execute(
                """
                SELECT id, warehouse_id, name, description, type, timestamp_created,
                       quantity, qr_code, min_quantity, location
                FROM items
                WHERE warehouse_id=%s
                ORDER BY name
                """,
                (self.id,),
            )
            rows = cur.fetchall()
            return [Item.from_row(r) for r in rows]

    def quantity_per_item(self, item: Union[int, str]) -> int:
        """
        item can be:
          - item_id (int)
          - qr_code (str)
        """
        from db.connection import db_cursor
        with db_cursor() as (_, cur):
            if isinstance(item, int):
                cur.execute(
                    "SELECT quantity FROM items WHERE id=%s AND warehouse_id=%s",
                    (item, self.id),
                )
            else:
                cur.execute(
                    "SELECT quantity FROM items WHERE qr_code=%s AND warehouse_id=%s",
                    (item.strip(), self.id),
                )
            row = cur.fetchone()
            return int(row["quantity"]) if row else 0

    # ---------- Stock operations (transactional) ----------
    def add_item(self, item_id: int, user_id: int, qty: int, note: str | None = None) -> None:
        self._apply_action(item_id=item_id, user_id=user_id, action="ADD", qty=qty, note=note)

    def remove_item(self, item_id: int, user_id: int, qty: int, note: str | None = None) -> None:
        self._apply_action(item_id=item_id, user_id=user_id, action="REMOVE", qty=qty, note=note)

    def return_item(self, item_id: int, user_id: int, qty: int, note: str | None = None) -> None:
        self._apply_action(item_id=item_id, user_id=user_id, action="RETURN", qty=qty, note=note)

    def _apply_action(self, item_id: int, user_id: int, action: str, qty: int, note: str | None) -> None:
        """
        Updates items.quantity and inserts warehouse_events row in one DB transaction.
        """
        if qty <= 0:
            raise ValueError("qty must be > 0")
        if action not in ("ADD", "REMOVE", "RETURN"):
            raise ValueError("Invalid action")

        delta = qty if action in ("ADD", "RETURN") else -qty

        from db.connection import db_cursor
        with db_cursor() as (_, cur):
            # lock item row to avoid double updates from multiple users
            cur.execute(
                """
                SELECT id, quantity
                FROM items
                WHERE id=%s AND warehouse_id=%s
                FOR UPDATE
                """,
                (item_id, self.id),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("Item not found in this warehouse")

            new_qty = int(row["quantity"]) + delta
            if new_qty < 0:
                raise ValueError("Not enough stock to remove")

            cur.execute(
                "UPDATE items SET quantity=%s WHERE id=%s",
                (new_qty, item_id),
            )

            cur.execute(
                """
                INSERT INTO warehouse_events (warehouse_id, item_id, user_id, action, quantity, note)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (self.id, item_id, user_id, action, qty, note),
            )
