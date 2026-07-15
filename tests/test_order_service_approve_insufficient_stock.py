from datetime import datetime

from app.models.order import OrderStatus
from app.models.sample import Sample
from app.repositories.order_repository import JsonOrderRepository
from app.repositories.sample_repository import JsonSampleRepository
from app.services.order_service import OrderService
from app.services.production_service import ProductionService

FIXED_NOW = datetime(2026, 4, 16, 9, 0, 0)


def make_service(tmp_path, stock: int, yield_rate: float = 0.8):
    sample_repository = JsonSampleRepository(tmp_path / "samples.json")
    sample_repository.create(
        Sample(
            sample_id="S-001",
            name="시료",
            avg_production_time=0.5,
            yield_rate=yield_rate,
            stock=stock,
        )
    )
    order_repository = JsonOrderRepository(tmp_path / "orders.json")
    production_service = ProductionService(clock=lambda: FIXED_NOW)
    service = OrderService(
        order_repository, sample_repository, production_service, clock=lambda: FIXED_NOW
    )
    return service, order_repository, sample_repository, production_service


def test_approve_with_insufficient_stock_transitions_to_producing(tmp_path):
    service, order_repository, _, _ = make_service(tmp_path, stock=0, yield_rate=0.8)
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=16)

    approved = service.approve(order.order_id)

    assert approved.status == OrderStatus.PRODUCING
    assert order_repository.get(order.order_id).status == OrderStatus.PRODUCING


def test_approve_with_insufficient_stock_enqueues_production_job(tmp_path):
    service, order_repository, _, production_service = make_service(tmp_path, stock=0, yield_rate=0.8)
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=16)

    service.approve(order.order_id)

    [job] = production_service.queue()
    assert job.order_id == order.order_id
    assert job.shortage == 16
    assert job.actual_quantity == 20  # ceil(16 / 0.8)


def test_approve_with_insufficient_stock_does_not_deduct_stock_yet(tmp_path):
    service, order_repository, sample_repository, _ = make_service(tmp_path, stock=5, yield_rate=0.8)
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=16)

    service.approve(order.order_id)

    # Stock isn't touched until production completes (Plan.md Step 5.2) --
    # only the (order.quantity - stock) shortage is computed and enqueued.
    assert sample_repository.get("S-001").stock == 5
