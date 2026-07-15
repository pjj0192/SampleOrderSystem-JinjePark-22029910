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
    return OrderService(
        order_repository, sample_repository, production_service, clock=lambda: FIXED_NOW
    )


def test_total_order_count_reflects_all_orders_regardless_of_status(tmp_path):
    service = make_service(tmp_path)
    assert service.total_order_count() == 0

    order = service.reserve(sample_id="S-001", customer_name="A", quantity=10)
    service.reserve(sample_id="S-001", customer_name="B", quantity=10)
    service.approve(order.order_id)

    assert service.total_order_count() == 2
