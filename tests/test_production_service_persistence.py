from datetime import datetime, timedelta

from app.models.order import Order, OrderStatus
from app.models.sample import Sample
from app.repositories.production_job_repository import JsonProductionJobRepository
from app.services.production_service import ProductionService

FIXED_NOW = datetime(2026, 4, 16, 9, 0, 0)


def make_order(order_id="ORD-0001", quantity=16):
    return Order(
        order_id=order_id,
        sample_id="S-001",
        customer_name="고객",
        quantity=quantity,
        status=OrderStatus.PRODUCING,
        created_at=FIXED_NOW,
        updated_at=FIXED_NOW,
    )


def make_sample(stock=0, yield_rate=0.8):
    return Sample(sample_id="S-001", name="시료", avg_production_time=0.5, yield_rate=yield_rate, stock=stock)


def test_enqueue_persists_job_to_repository(tmp_path):
    repo = JsonProductionJobRepository(tmp_path / "queue.json")
    service = ProductionService(clock=lambda: FIXED_NOW, repository=repo)

    job = service.enqueue(order=make_order(), sample=make_sample())

    [persisted] = repo.list_all()
    assert persisted.job_id == job.job_id
    assert persisted.started_at == FIXED_NOW  # became current immediately


def test_second_enqueued_job_persists_without_started_at(tmp_path):
    repo = JsonProductionJobRepository(tmp_path / "queue.json")
    service = ProductionService(clock=lambda: FIXED_NOW, repository=repo)

    service.enqueue(order=make_order("ORD-0001"), sample=make_sample())
    service.enqueue(order=make_order("ORD-0002"), sample=make_sample())

    waiting_job = next(j for j in repo.list_all() if j.order_id == "ORD-0002")
    assert waiting_job.started_at is None


def test_restarting_service_from_repository_restores_current_and_waiting(tmp_path):
    path = tmp_path / "queue.json"
    repo = JsonProductionJobRepository(path)
    service = ProductionService(clock=lambda: FIXED_NOW, repository=repo)
    first = service.enqueue(order=make_order("ORD-0001"), sample=make_sample())
    second = service.enqueue(order=make_order("ORD-0002"), sample=make_sample())

    restarted = ProductionService(
        clock=lambda: FIXED_NOW, repository=JsonProductionJobRepository(path)
    )

    current, waiting = restarted.current_and_queue()
    assert current.job_id == first.job_id
    assert [j.job_id for j in waiting] == [second.job_id]


def test_advance_deletes_completed_job_from_repository(tmp_path):
    path = tmp_path / "queue.json"
    repo = JsonProductionJobRepository(path)
    clock_values = iter([FIXED_NOW, FIXED_NOW + timedelta(seconds=10)])
    service = ProductionService(clock=lambda: next(clock_values), minute_duration_seconds=1, repository=repo)
    service.enqueue(order=make_order(), sample=make_sample())

    service.advance()

    assert repo.list_all() == []


def test_next_job_number_continues_after_restart(tmp_path):
    path = tmp_path / "queue.json"
    repo = JsonProductionJobRepository(path)
    service = ProductionService(clock=lambda: FIXED_NOW, repository=repo)
    service.enqueue(order=make_order("ORD-0001"), sample=make_sample())

    restarted = ProductionService(
        clock=lambda: FIXED_NOW, repository=JsonProductionJobRepository(path)
    )
    new_job = restarted.enqueue(order=make_order("ORD-0002"), sample=make_sample())

    assert new_job.job_id == "JOB-0002"
