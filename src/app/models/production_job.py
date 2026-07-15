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
