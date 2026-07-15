from datetime import datetime

from app.models.order import Order, OrderStatus
from app.models.sample import Sample
from app.repositories.order_repository import JsonOrderRepository
from app.repositories.sample_repository import JsonSampleRepository
from app.services.order_service import OrderService
from app.services.production_service import ProductionService

FIXED_NOW = datetime(2026, 4, 16, 9, 0, 0)


def make_service(tmp_path):
    sample_repository = JsonSampleRepository(tmp_path / "samples.json")
    sample_repository.create(
        Sample(sample_id="S-001", name="시료", avg_production_time=0.5, yield_rate=0.8, stock=0)
    )
    order_repository = JsonOrderRepository(tmp_path / "orders.json")
    production_service = ProductionService(clock=lambda: FIXED_NOW, minute_duration_seconds=1)
    service = OrderService(
        order_repository, sample_repository, production_service, clock=lambda: FIXED_NOW
    )
    return service, order_repository, production_service


def test_resync_reenqueues_producing_order_with_no_matching_job(tmp_path):
    """Reproduces the 'monitoring shows PRODUCING but nothing is actually
    producing' symptom: an order was already PRODUCING in orders.json (e.g.
    persisted before the production queue itself was persisted), but the
    in-memory/persisted queue has no job for it."""
    service, order_repository, production_service = make_service(tmp_path)
    orphaned_order = Order(
        order_id="ORD-0001",
        sample_id="S-001",
        customer_name="고객",
        quantity=16,
        status=OrderStatus.PRODUCING,
        created_at=FIXED_NOW,
        updated_at=FIXED_NOW,
    )
    order_repository.create(orphaned_order)
    assert production_service.queue() == []

    service.resync_production_queue()

    [job] = production_service.queue()
    assert job.order_id == "ORD-0001"
    assert job.shortage == 16  # 16 - stock(0)


def test_resync_does_not_duplicate_job_for_order_already_queued(tmp_path):
    service, order_repository, production_service = make_service(tmp_path)
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=16)
    service.approve(order.order_id)  # already enqueues a job (stock=0 < 16)
    assert len(production_service.queue()) == 1

    service.resync_production_queue()

    assert len(production_service.queue()) == 1


def test_resync_ignores_orders_not_in_producing_status(tmp_path):
    service, order_repository, production_service = make_service(tmp_path)
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=16)

    service.resync_production_queue()

    assert production_service.queue() == []
    assert order_repository.get(order.order_id).status == OrderStatus.RESERVED
