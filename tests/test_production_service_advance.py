from datetime import datetime

from app.models.order import Order, OrderStatus
from app.models.sample import Sample
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


def test_advance_returns_and_removes_the_front_job():
    service = ProductionService(clock=lambda: FIXED_NOW)
    first = service.enqueue(order=make_order("ORD-0001"), sample=make_sample())
    service.enqueue(order=make_order("ORD-0002"), sample=make_sample())

    completed = service.advance()

    assert completed.job_id == first.job_id
    assert [job.order_id for job in service.queue()] == ["ORD-0002"]


def test_advance_returns_none_when_queue_is_empty():
    service = ProductionService(clock=lambda: FIXED_NOW)

    assert service.advance() is None
