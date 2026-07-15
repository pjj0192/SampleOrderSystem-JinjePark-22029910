from datetime import datetime, timedelta
from unittest.mock import Mock

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


def test_advance_returns_none_when_job_not_yet_complete():
    # total_time = 0.5 * ceil(16/0.8) = 0.5 * 20 = 10 minutes.
    # Test mode: minute_duration_seconds=1 -> needs >=10 elapsed seconds.
    # Only 5 seconds have passed, so it isn't done yet.
    clock = Mock(side_effect=[FIXED_NOW, FIXED_NOW + timedelta(seconds=5)])
    service = ProductionService(clock=clock, minute_duration_seconds=1)
    service.enqueue(order=make_order(), sample=make_sample())

    assert service.advance() is None


def test_advance_completes_job_once_elapsed_time_reaches_total_time():
    clock = Mock(side_effect=[FIXED_NOW, FIXED_NOW + timedelta(seconds=10)])
    service = ProductionService(clock=clock, minute_duration_seconds=1)
    job = service.enqueue(order=make_order(), sample=make_sample())

    completed = service.advance()

    assert completed.job_id == job.job_id


def test_advance_returns_none_when_queue_is_empty():
    service = ProductionService(clock=lambda: FIXED_NOW, minute_duration_seconds=1)

    assert service.advance() is None


def test_advance_promotes_next_waiting_job_after_completion():
    later = FIXED_NOW + timedelta(seconds=10)
    clock = Mock(
        side_effect=[
            FIXED_NOW,  # enqueue first (becomes current, starts now)
            FIXED_NOW,  # enqueue second (stays waiting)
            later,  # advance(): checks first's elapsed time -> done
            later,  # advance(): records the promoted job's new start time
            later,  # current_and_queue(): progress check for the promoted job
        ]
    )
    service = ProductionService(clock=clock, minute_duration_seconds=1)
    first = service.enqueue(order=make_order("ORD-0001"), sample=make_sample())
    second = service.enqueue(order=make_order("ORD-0002"), sample=make_sample())

    completed = service.advance()

    assert completed.job_id == first.job_id
    current, waiting = service.current_and_queue()
    assert current.job_id == second.job_id
    assert waiting == []
