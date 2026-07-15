from datetime import datetime

from app.models.order import OrderStatus
from app.models.sample import Sample
from app.repositories.order_repository import JsonOrderRepository
from app.repositories.sample_repository import JsonSampleRepository
from app.services.order_service import OrderService
from app.services.production_service import ProductionService

FIXED_NOW = datetime(2026, 4, 16, 9, 0, 0)


def make_service(tmp_path, stock: int = 100):
    sample_repository = JsonSampleRepository(tmp_path / "samples.json")
    sample_repository.create(
        Sample(sample_id="S-001", name="시료", avg_production_time=0.5, yield_rate=0.9, stock=stock)
    )
    order_repository = JsonOrderRepository(tmp_path / "orders.json")
    production_service = ProductionService(clock=lambda: FIXED_NOW)
    service = OrderService(
        order_repository, sample_repository, production_service, clock=lambda: FIXED_NOW
    )
    return service, order_repository, sample_repository, production_service


def test_reject_transitions_to_rejected(tmp_path):
    service, order_repository, _, _ = make_service(tmp_path)
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)

    rejected = service.reject(order.order_id)

    assert rejected.status == OrderStatus.REJECTED
    assert order_repository.get(order.order_id).status == OrderStatus.REJECTED


def test_reject_does_not_touch_stock(tmp_path):
    service, order_repository, sample_repository, _ = make_service(tmp_path, stock=100)
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)

    service.reject(order.order_id)

    assert sample_repository.get("S-001").stock == 100


def test_reject_does_not_enqueue_production_job(tmp_path):
    service, order_repository, _, production_service = make_service(tmp_path)
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)

    service.reject(order.order_id)

    assert production_service.queue() == []
