from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProductionJob:
    job_id: str
    order_id: str
    sample_id: str
    shortage: int
    actual_quantity: int
    total_time: float
    enqueued_at: datetime
    started_at: datetime | None = None
    progress: float = 0.0

    def __post_init__(self) -> None:
        if not self.job_id or not self.job_id.strip():
            raise ValueError("job_id must not be blank")
        if not self.order_id or not self.order_id.strip():
            raise ValueError("order_id must not be blank")
        if not self.sample_id or not self.sample_id.strip():
            raise ValueError("sample_id must not be blank")
        if self.shortage <= 0:
            raise ValueError("shortage must be positive")
        if self.actual_quantity <= 0:
            raise ValueError("actual_quantity must be positive")
        if self.actual_quantity < self.shortage:
            raise ValueError("actual_quantity must be >= shortage")
        if self.total_time <= 0:
            raise ValueError("total_time must be positive")
        if not (0 <= self.progress <= 1):
            raise ValueError("progress must be within [0, 1]")

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "order_id": self.order_id,
            "sample_id": self.sample_id,
            "shortage": self.shortage,
            "actual_quantity": self.actual_quantity,
            "total_time": self.total_time,
            "enqueued_at": self.enqueued_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at is not None else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProductionJob":
        return cls(
            job_id=data["job_id"],
            order_id=data["order_id"],
            sample_id=data["sample_id"],
            shortage=data["shortage"],
            actual_quantity=data["actual_quantity"],
            total_time=data["total_time"],
            enqueued_at=datetime.fromisoformat(data["enqueued_at"]),
            started_at=(
                datetime.fromisoformat(data["started_at"])
                if data.get("started_at") is not None
                else None
            ),
        )
