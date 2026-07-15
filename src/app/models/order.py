from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class OrderStatus(Enum):
    RESERVED = "RESERVED"
    REJECTED = "REJECTED"
    PRODUCING = "PRODUCING"
    CONFIRMED = "CONFIRMED"
    RELEASED = "RELEASED"


@dataclass
class Order:
    order_id: str
    sample_id: str
    customer_name: str
    quantity: int
    status: OrderStatus
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not self.order_id or not self.order_id.strip():
            raise ValueError("order_id must not be blank")
        if not self.sample_id or not self.sample_id.strip():
            raise ValueError("sample_id must not be blank")
        if not self.customer_name or not self.customer_name.strip():
            raise ValueError("customer_name must not be blank")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")

    def to_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "sample_id": self.sample_id,
            "customer_name": self.customer_name,
            "quantity": self.quantity,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Order":
        return cls(
            order_id=data["order_id"],
            sample_id=data["sample_id"],
            customer_name=data["customer_name"],
            quantity=data["quantity"],
            status=OrderStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
