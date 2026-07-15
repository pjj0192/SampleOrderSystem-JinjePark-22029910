import math
from collections import deque
from collections.abc import Callable
from datetime import datetime

from app.models.order import Order
from app.models.production_job import ProductionJob
from app.models.sample import Sample


class ProductionService:
    """Owns the single FIFO production queue (PRD.md §7.5). shortage/
    actual_quantity/total_time are computed here, not in ProductionJob
    itself, so the model stays a plain value object."""

    def __init__(self, clock: Callable[[], datetime] = datetime.now) -> None:
        self._clock = clock
        self._queue: deque[ProductionJob] = deque()
        self._next_job_number = 1

    def enqueue(self, order: Order, sample: Sample) -> ProductionJob:
        shortage = order.quantity - sample.stock
        actual_quantity = math.ceil(shortage / sample.yield_rate)
        total_time = sample.avg_production_time * actual_quantity

        job = ProductionJob(
            job_id=f"JOB-{self._next_job_number:04d}",
            order_id=order.order_id,
            sample_id=sample.sample_id,
            shortage=shortage,
            actual_quantity=actual_quantity,
            total_time=total_time,
            enqueued_at=self._clock(),
        )
        self._next_job_number += 1
        self._queue.append(job)
        return job

    def queue(self) -> list[ProductionJob]:
        return list(self._queue)

    def current_and_queue(self) -> tuple[ProductionJob | None, list[ProductionJob]]:
        """Splits the FIFO queue into the job that would be completed next
        (the "currently processing" job in PRD.md §7.5's UI example) and
        the jobs still waiting behind it."""
        if not self._queue:
            return None, []
        jobs = list(self._queue)
        return jobs[0], jobs[1:]

    def advance(self) -> ProductionJob | None:
        """Completes the job at the front of the FIFO queue (this
        simulation treats production as finishing all-at-once rather than
        ticking progress over time) and returns it, or None if the queue
        is empty."""
        if not self._queue:
            return None
        return self._queue.popleft()
