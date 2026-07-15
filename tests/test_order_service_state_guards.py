from datetime import datetime

import pytest

from app.models.sample import Sample
from app.repositories.order_repository import JsonOrderRepository
from app.repositories.sample_repository import JsonSampleRepository
from app.services.order_service import InvalidOrderStateError, OrderService
from app.services.production_service import ProductionService

FIXED_NOW = datetime(2026, 4, 16, 9, 0, 0)


def make_service(tmp_path, stock: int = 300):
    sample_repository = JsonSampleRepository(tmp_path / "samples.json")
    sample_repository.create(
        Sample(sample_id="S-001", name="시료", avg_production_time=0.5, yield_rate=0.9, stock=stock)
    )
    order_repository = JsonOrderRepository(tmp_path / "orders.json")
    production_service = ProductionService(clock=lambda: FIXED_NOW)
    service = OrderService(
        order_repository, sample_repository, production_service, clock=lambda: FIXED_NOW
    )
    return service, order_repository, sample_repository


def test_approve_rejects_order_not_in_reserved_state(tmp_path):
    service, _, _ = make_service(tmp_path, stock=300)
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)
    service.approve(order.order_id)  # RESERVED -> CONFIRMED

    with pytest.raises(InvalidOrderStateError):
        service.approve(order.order_id)  # already CONFIRMED


def test_approve_twice_does_not_double_deduct_stock(tmp_path):
    service, _, sample_repository = make_service(tmp_path, stock=300)
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)
    service.approve(order.order_id)

    with pytest.raises(InvalidOrderStateError):
        service.approve(order.order_id)

    assert sample_repository.get("S-001").stock == 290


def test_reject_rejects_order_not_in_reserved_state(tmp_path):
    service, _, _ = make_service(tmp_path, stock=300)
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)
    service.reject(order.order_id)  # RESERVED -> REJECTED

    with pytest.raises(InvalidOrderStateError):
        service.reject(order.order_id)  # already REJECTED
