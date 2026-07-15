from datetime import datetime

import pytest

from app.models.order import OrderStatus
from app.models.sample import Sample
from app.repositories.order_repository import JsonOrderRepository
from app.repositories.sample_repository import JsonSampleRepository, SampleNotFoundError
from app.services.order_service import OrderService
from app.services.production_service import ProductionService

FIXED_NOW = datetime(2026, 4, 16, 9, 0, 0)


def make_service(tmp_path, existing_sample=True):
    sample_repository = JsonSampleRepository(tmp_path / "samples.json")
    if existing_sample:
        sample_repository.create(
            Sample(sample_id="S-001", name="실리콘 웨이퍼-8인치", avg_production_time=0.5, yield_rate=0.92)
        )
    order_repository = JsonOrderRepository(tmp_path / "orders.json")
    production_service = ProductionService(clock=lambda: FIXED_NOW)
    service = OrderService(
        order_repository, sample_repository, production_service, clock=lambda: FIXED_NOW
    )
    return service, order_repository


def test_reserve_creates_order_with_reserved_status(tmp_path):
    service, order_repository = make_service(tmp_path)

    order = service.reserve(sample_id="S-001", customer_name="삼성전자 파운드리", quantity=200)

    assert order.status == OrderStatus.RESERVED
    assert order.sample_id == "S-001"
    assert order.quantity == 200
    assert order_repository.get(order.order_id) == order


def test_reserve_generates_unique_order_ids(tmp_path):
    service, _ = make_service(tmp_path)

    first = service.reserve(sample_id="S-001", customer_name="A", quantity=10)
    second = service.reserve(sample_id="S-001", customer_name="B", quantity=20)

    assert first.order_id != second.order_id


def test_reserve_rejects_unknown_sample_id(tmp_path):
    service, _ = make_service(tmp_path)

    with pytest.raises(SampleNotFoundError):
        service.reserve(sample_id="S-999", customer_name="고객", quantity=10)


def test_reserve_rejects_non_positive_quantity(tmp_path):
    service, _ = make_service(tmp_path)

    with pytest.raises(ValueError):
        service.reserve(sample_id="S-001", customer_name="고객", quantity=0)
