from datetime import datetime

from app.models.sample import Sample
from app.repositories.order_repository import JsonOrderRepository
from app.repositories.sample_repository import JsonSampleRepository
from app.services.order_service import OrderService
from app.services.production_service import ProductionService

FIXED_NOW = datetime(2026, 4, 16, 9, 0, 0)


def make_service(tmp_path):
    sample_repository = JsonSampleRepository(tmp_path / "samples.json")
    sample_repository.create(
        Sample(sample_id="S-001", name="시료", avg_production_time=0.5, yield_rate=0.9, stock=300)
    )
    order_repository = JsonOrderRepository(tmp_path / "orders.json")
    production_service = ProductionService(clock=lambda: FIXED_NOW)
    service = OrderService(
        order_repository, sample_repository, production_service, clock=lambda: FIXED_NOW
    )
    return service


def test_list_reserved_returns_only_reserved_orders(tmp_path):
    service = make_service(tmp_path)
    reserved = service.reserve(sample_id="S-001", customer_name="A", quantity=10)
    to_approve = service.reserve(sample_id="S-001", customer_name="B", quantity=10)
    service.approve(to_approve.order_id)

    result = service.list_reserved()

    assert [o.order_id for o in result] == [reserved.order_id]


def test_list_reserved_returns_empty_list_when_none_pending(tmp_path):
    service = make_service(tmp_path)

    assert service.list_reserved() == []
