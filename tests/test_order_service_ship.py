from datetime import datetime

import pytest

from app.models.order import OrderStatus
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


def test_ship_confirmed_order_transitions_to_released(tmp_path):
    service, order_repository, _ = make_service(tmp_path)
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)
    service.approve(order.order_id)

    shipped = service.ship(order.order_id)

    assert shipped.status == OrderStatus.RELEASED
    assert order_repository.get(order.order_id).status == OrderStatus.RELEASED


def test_ship_does_not_change_stock(tmp_path):
    service, order_repository, sample_repository = make_service(tmp_path, stock=300)
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)
    service.approve(order.order_id)
    stock_after_approval = sample_repository.get("S-001").stock

    service.ship(order.order_id)

    assert sample_repository.get("S-001").stock == stock_after_approval


def test_ship_rejects_order_not_in_confirmed_state(tmp_path):
    service, order_repository, _ = make_service(tmp_path)
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)  # still RESERVED

    with pytest.raises(InvalidOrderStateError):
        service.ship(order.order_id)
