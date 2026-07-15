import math
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime

from app.models.order import Order
from app.models.production_job import ProductionJob
from app.models.sample import Sample

REAL_TIME_SECONDS_PER_MINUTE = 60.0


@dataclass(frozen=True)
class ProductionEstimate:
    """shortage/actual_quantity/total_time for a given (quantity, stock,
    avg_production_time, yield_rate) combination -- the same formula
    enqueue() uses to build a ProductionJob, exposed standalone so a
    preview (e.g. before an approval decision) can show identical numbers
    without actually enqueuing anything."""

    shortage: int
    actual_quantity: int
    total_time: float


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
        repository=None,
    ) -> None:
        self._clock = clock
        self._minute_duration_seconds = minute_duration_seconds
        self._repository = repository
        self._current: ProductionJob | None = None
        self._waiting: deque[ProductionJob] = deque()
        self._next_job_number = 1
        if repository is not None:
            self._restore_from_repository()

    @property
    def minute_duration_seconds(self) -> float:
        return self._minute_duration_seconds

    def _restore_from_repository(self) -> None:
        """Rebuilds the FIFO queue from persisted jobs (oldest enqueued_at
        first) so orders left at PRODUCING survive an app restart instead
        of being stuck forever with no job actually driving them to
        completion."""
        jobs = sorted(self._repository.list_all(), key=lambda job: job.enqueued_at)
        for job in jobs:
            job_number = int(job.job_id.rsplit("-", 1)[-1])
            self._next_job_number = max(self._next_job_number, job_number + 1)
        if not jobs:
            return
        current, *waiting = jobs
        if current.started_at is None:
            current = replace(current, started_at=self._clock())
            self._repository.update(current)
        self._current = current
        self._waiting = deque(waiting)

    @staticmethod
    def estimate_production(
        quantity: int, stock: int, avg_production_time: float, yield_rate: float
    ) -> ProductionEstimate:
        shortage = max(quantity - stock, 0)
        if shortage == 0:
            return ProductionEstimate(shortage=0, actual_quantity=0, total_time=0.0)
        actual_quantity = math.ceil(shortage / yield_rate)
        total_time = avg_production_time * actual_quantity
        return ProductionEstimate(
            shortage=shortage, actual_quantity=actual_quantity, total_time=total_time
        )

    def enqueue(self, order: Order, sample: Sample) -> ProductionJob:
        estimate = self.estimate_production(
            order.quantity, sample.stock, sample.avg_production_time, sample.yield_rate
        )
        now = self._clock()
        becomes_current = self._current is None

        job = ProductionJob(
            job_id=f"JOB-{self._next_job_number:04d}",
            order_id=order.order_id,
            sample_id=sample.sample_id,
            shortage=estimate.shortage,
            actual_quantity=estimate.actual_quantity,
            total_time=estimate.total_time,
            enqueued_at=now,
            started_at=now if becomes_current else None,
        )
        self._next_job_number += 1
        if self._repository is not None:
            self._repository.create(job)

        if becomes_current:
            self._current = job
        else:
            self._waiting.append(job)
        return job

    def queue(self) -> list[ProductionJob]:
        jobs = [self._current] if self._current is not None else []
        jobs.extend(self._waiting)
        return jobs

    def _elapsed_minutes(self) -> float:
        if self._current is None or self._current.started_at is None:
            return 0.0
        elapsed_seconds = (self._clock() - self._current.started_at).total_seconds()
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
        if self._repository is not None:
            self._repository.delete(completed.job_id)

        if self._waiting:
            promoted = replace(self._waiting.popleft(), started_at=self._clock())
            if self._repository is not None:
                self._repository.update(promoted)
            self._current = promoted
        else:
            self._current = None
        return completed
