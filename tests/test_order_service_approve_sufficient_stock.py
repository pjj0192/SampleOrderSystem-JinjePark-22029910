from datetime import datetime

from app.models.order import OrderStatus
from app.models.sample import Sample
from app.repositories.order_repository import JsonOrderRepository
from app.repositories.sample_repository import JsonSampleRepository
from app.services.order_service import OrderService

FIXED_NOW = datetime(2026, 4, 16, 9, 0, 0)


def make_service(tmp_path, stock: int):
    sample_repository = JsonSampleRepository(tmp_path / "samples.json")
    sample_repository.create(
        Sample(
            sample_id="S-001",
            name="실리콘 웨이퍼-8인치",
            avg_production_time=0.5,
            yield_rate=0.92,
            stock=stock,
        )
    )
    order_repository = JsonOrderRepository(tmp_path / "orders.json")
    service = OrderService(order_repository, sample_repository, clock=lambda: FIXED_NOW)
    return service, order_repository, sample_repository


def test_approve_with_sufficient_stock_confirms_immediately(tmp_path):
    service, order_repository, sample_repository = make_service(tmp_path, stock=300)
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=200)

    approved = service.approve(order.order_id)

    assert approved.status == OrderStatus.CONFIRMED
    assert order_repository.get(order.order_id).status == OrderStatus.CONFIRMED


def test_approve_with_sufficient_stock_deducts_quantity_from_stock(tmp_path):
    service, order_repository, sample_repository = make_service(tmp_path, stock=300)
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=200)

    service.approve(order.order_id)

    assert sample_repository.get("S-001").stock == 100


def test_approve_with_exactly_matching_stock_confirms(tmp_path):
    service, order_repository, sample_repository = make_service(tmp_path, stock=200)
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=200)

    approved = service.approve(order.order_id)

    assert approved.status == OrderStatus.CONFIRMED
    assert sample_repository.get("S-001").stock == 0
