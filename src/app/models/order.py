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
