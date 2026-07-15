from datetime import datetime

from app.models.order import Order, OrderStatus
from app.models.sample import Sample
from app.services.production_service import ProductionService

FIXED_NOW = datetime(2026, 4, 16, 9, 0, 0)


def make_order(quantity=16):
    return Order(
        order_id="ORD-0001",
        sample_id="S-001",
        customer_name="고객",
        quantity=quantity,
        status=OrderStatus.PRODUCING,
        created_at=FIXED_NOW,
        updated_at=FIXED_NOW,
    )


def make_sample(stock=0, yield_rate=0.8, avg_production_time=0.5):
    return Sample(
        sample_id="S-001",
        name="시료",
        avg_production_time=avg_production_time,
        yield_rate=yield_rate,
        stock=stock,
    )


def test_enqueue_computes_actual_quantity_via_ceil_of_shortage_over_yield():
    service = ProductionService(clock=lambda: FIXED_NOW)

    job = service.enqueue(order=make_order(quantity=16), sample=make_sample(stock=0, yield_rate=0.8))

    assert job.shortage == 16
    assert job.actual_quantity == 20  # ceil(16 / 0.8)


def test_enqueue_computes_total_time_from_avg_production_time():
    service = ProductionService(clock=lambda: FIXED_NOW)

    job = service.enqueue(
        order=make_order(quantity=16), sample=make_sample(stock=0, yield_rate=0.8, avg_production_time=0.5)
    )

    assert job.total_time == 10.0  # 0.5 * 20


def test_enqueue_accounts_for_existing_stock_in_shortage():
    service = ProductionService(clock=lambda: FIXED_NOW)

    job = service.enqueue(order=make_order(quantity=80), sample=make_sample(stock=30, yield_rate=0.92))

    assert job.shortage == 50


def test_enqueue_adds_job_to_fifo_queue():
    service = ProductionService(clock=lambda: FIXED_NOW)

    first = service.enqueue(order=make_order(quantity=16), sample=make_sample(stock=0))
    second = service.enqueue(order=make_order(quantity=8), sample=make_sample(stock=0))

    queue = service.queue()
    assert [job.job_id for job in queue] == [first.job_id, second.job_id]


def test_enqueue_generates_unique_job_ids():
    service = ProductionService(clock=lambda: FIXED_NOW)

    first = service.enqueue(order=make_order(), sample=make_sample(stock=0))
    second = service.enqueue(order=make_order(), sample=make_sample(stock=0))

    assert first.job_id != second.job_id
