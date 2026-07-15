from datetime import datetime

from app.models.order import Order, OrderStatus
from app.models.sample import Sample
from app.services.production_service import ProductionService

FIXED_NOW = datetime(2026, 4, 16, 9, 0, 0)


def make_order(order_id="ORD-0001"):
    return Order(
        order_id=order_id,
        sample_id="S-001",
        customer_name="고객",
        quantity=16,
        status=OrderStatus.PRODUCING,
        created_at=FIXED_NOW,
        updated_at=FIXED_NOW,
    )


def make_sample():
    return Sample(sample_id="S-001", name="시료", avg_production_time=0.5, yield_rate=0.8, stock=0)


def test_current_and_queue_splits_front_job_from_the_rest():
    service = ProductionService(clock=lambda: FIXED_NOW)
    first = service.enqueue(order=make_order("ORD-0001"), sample=make_sample())
    second = service.enqueue(order=make_order("ORD-0002"), sample=make_sample())
    third = service.enqueue(order=make_order("ORD-0003"), sample=make_sample())

    current, waiting = service.current_and_queue()

    assert current.job_id == first.job_id
    assert [job.job_id for job in waiting] == [second.job_id, third.job_id]


def test_current_and_queue_returns_none_current_when_empty():
    service = ProductionService(clock=lambda: FIXED_NOW)

    current, waiting = service.current_and_queue()

    assert current is None
    assert waiting == []
