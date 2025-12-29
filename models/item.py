from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Item:
    id: int
    sku: str
    name: str
    type: str
    description: Optional[str]
    quantity: int
    min_quantity: int
    location: Optional[str]
    warehouse_id: int
    qr_code: Optional[str]
    timestamp_created: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: dict) -> "Item":
        return cls(
            id=row["id"],
            sku=row["sku"],
            name=row["name"],
            type=row["type"],
            description=row.get("description"),
            quantity=row["quantity"],
            min_quantity=row["min_quantity"],
            location=row.get("location"),
            warehouse_id=row["warehouse_id"],
            qr_code=row.get("qr_code"),
            timestamp_created=row["timestamp_created"],
            updated_at=row["updated_at"],
        )
