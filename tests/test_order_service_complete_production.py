from datetime import datetime, timedelta
from unittest.mock import Mock

from app.models.order import OrderStatus
from app.models.sample import Sample
from app.repositories.order_repository import JsonOrderRepository
from app.repositories.sample_repository import JsonSampleRepository
from app.services.order_service import OrderService
from app.services.production_service import ProductionService

FIXED_NOW = datetime(2026, 4, 16, 9, 0, 0)

# Comfortably longer than any total_time used in these tests (minutes), so
# with minute_duration_seconds=1 (test mode) the enqueued job always reads
# as complete by the time complete_production() checks it.
ELAPSED_SECONDS_ENOUGH_TO_FINISH = 100_000


def make_service(tmp_path, stock: int, yield_rate: float):
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
    production_clock = Mock(
        side_effect=[FIXED_NOW, FIXED_NOW + timedelta(seconds=ELAPSED_SECONDS_ENOUGH_TO_FINISH)]
    )
    production_service = ProductionService(clock=production_clock, minute_duration_seconds=1)
    service = OrderService(
        order_repository, sample_repository, production_service, clock=lambda: FIXED_NOW
    )
    return service, order_repository, sample_repository


def test_complete_production_matches_prd_example(tmp_path):
    """PRD.md §7.5: order 16, stock 0, yield 0.8 -> actual_quantity 20 ->
    stock goes 0 -> 20 (full receipt) -> 4 (after deducting the order) ->
    CONFIRMED, leaving 4 as surplus."""
    service, order_repository, sample_repository = make_service(tmp_path, stock=0, yield_rate=0.8)
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=16)
    service.approve(order.order_id)  # insufficient stock -> PRODUCING, enqueued

    completed = service.complete_production()

    assert completed.status == OrderStatus.CONFIRMED
    assert order_repository.get(order.order_id).status == OrderStatus.CONFIRMED
    assert sample_repository.get("S-001").stock == 4


def test_complete_production_with_partial_existing_stock(tmp_path):
    # order 80, stock 30, yield 0.92 -> shortage 50 -> actual_quantity ceil(50/0.92)=55
    # stock: 30 + 55 = 85, then -80 (order) = 5 surplus
    service, order_repository, sample_repository = make_service(tmp_path, stock=30, yield_rate=0.92)
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=80)
    service.approve(order.order_id)

    service.complete_production()

    assert sample_repository.get("S-001").stock == 5


def test_complete_production_returns_none_when_nothing_queued(tmp_path):
    service, _, _ = make_service(tmp_path, stock=100, yield_rate=0.9)

    assert service.complete_production() is None
