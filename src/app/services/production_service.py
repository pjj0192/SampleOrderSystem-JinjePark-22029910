import math
from collections import deque
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime

from app.models.order import Order
from app.models.production_job import ProductionJob
from app.models.sample import Sample

REAL_TIME_SECONDS_PER_MINUTE = 60.0


class ProductionService:
    """Owns the single FIFO production queue (PRD.md §7.5). shortage/
    actual_quantity/total_time are computed here, not in ProductionJob
    itself, so the model stays a plain value object.

    Production now takes real elapsed time to finish: a job's total_time
    (in minutes) must actually elapse before advance() will complete it.
    minute_duration_seconds controls how many real seconds equal one
    "production minute" -- 60 (default) for real-time behavior, 1 for a
    fast test/demo mode. Tests drive elapsed time via an injected clock
    (see tests/test_production_service_advance.py) rather than actually
    sleeping.
    """

    def __init__(
        self,
        clock: Callable[[], datetime] = datetime.now,
        minute_duration_seconds: float = REAL_TIME_SECONDS_PER_MINUTE,
    ) -> None:
        self._clock = clock
        self._minute_duration_seconds = minute_duration_seconds
        self._current: ProductionJob | None = None
        self._current_started_at: datetime | None = None
        self._waiting: deque[ProductionJob] = deque()
        self._next_job_number = 1

    def enqueue(self, order: Order, sample: Sample) -> ProductionJob:
        shortage = order.quantity - sample.stock
        actual_quantity = math.ceil(shortage / sample.yield_rate)
        total_time = sample.avg_production_time * actual_quantity
        now = self._clock()

        job = ProductionJob(
            job_id=f"JOB-{self._next_job_number:04d}",
            order_id=order.order_id,
            sample_id=sample.sample_id,
            shortage=shortage,
            actual_quantity=actual_quantity,
            total_time=total_time,
            enqueued_at=now,
        )
        self._next_job_number += 1

        if self._current is None:
            self._current = job
            self._current_started_at = now
        else:
            self._waiting.append(job)
        return job

    def queue(self) -> list[ProductionJob]:
        jobs = [self._current] if self._current is not None else []
        jobs.extend(self._waiting)
        return jobs

    def _elapsed_minutes(self) -> float:
        if self._current is None or self._current_started_at is None:
            return 0.0
        elapsed_seconds = (self._clock() - self._current_started_at).total_seconds()
        return elapsed_seconds / self._minute_duration_seconds

    def current_and_queue(self) -> tuple[ProductionJob | None, list[ProductionJob]]:
        """Splits the queue into the job currently being processed (with its
        live progress filled in based on elapsed real time) and the jobs
        still waiting behind it."""
        if self._current is None:
            return None, list(self._waiting)
        progress = min(self._elapsed_minutes() / self._current.total_time, 1.0)
        current_with_progress = replace(self._current, progress=progress)
        return current_with_progress, list(self._waiting)

    def advance(self) -> ProductionJob | None:
        """Completes the current job only once its total_time (in minutes)
        has actually elapsed, and promotes the next waiting job to current.
        Returns None if nothing is queued, or if the current job isn't
        finished yet."""
        if self._current is None:
            return None
        if self._elapsed_minutes() < self._current.total_time:
            return None

        completed = self._current
        if self._waiting:
            self._current = self._waiting.popleft()
            self._current_started_at = self._clock()
        else:
            self._current = None
            self._current_started_at = None
        return completed
