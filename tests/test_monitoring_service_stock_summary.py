from datetime import datetime

from app.models.order import Order, OrderStatus
from app.models.sample import Sample
from app.services.monitoring_service import MonitoringService

FIXED_NOW = datetime(2026, 4, 16, 9, 0, 0)


class FakeSampleRepository:
    def __init__(self, samples: list[Sample]) -> None:
        self._samples = samples

    def list_all(self) -> list[Sample]:
        return self._samples

    def get(self, sample_id: str):
        return next((s for s in self._samples if s.sample_id == sample_id), None)


class FakeOrderRepository:
    def __init__(self, orders: list[Order]) -> None:
        self._orders = orders

    def list_all(self) -> list[Order]:
        return self._orders

    def list_by_sample(self, sample_id: str) -> list[Order]:
        return [o for o in self._orders if o.sample_id == sample_id]


def _sample(sample_id="S-001", name="시료A", stock=0):
    return Sample(
        sample_id=sample_id, name=name, avg_production_time=1.0, yield_rate=0.9, stock=stock
    )


def _order(sample_id, quantity, status):
    return Order(
        order_id="ORD",
        sample_id=sample_id,
        customer_name="고객",
        quantity=quantity,
        status=status,
        created_at=FIXED_NOW,
        updated_at=FIXED_NOW,
    )


def test_ratio_exactly_50_percent_is_classified_as_sufficient():
    samples = [_sample(stock=50)]
    orders = [_order("S-001", 100, OrderStatus.RESERVED)]
    service = MonitoringService(FakeSampleRepository(samples), FakeOrderRepository(orders))

    [entry] = service.stock_summary()

    assert entry["ratio"] == 0.5
    assert entry["status"] == "여유"


def test_stock_zero_is_depleted_regardless_of_pending_demand():
    samples = [_sample(stock=0)]
    orders: list[Order] = []
    service = MonitoringService(FakeSampleRepository(samples), FakeOrderRepository(orders))

    [entry] = service.stock_summary()

    assert entry["status"] == "고갈"


def test_ratio_below_50_percent_is_classified_as_short():
    samples = [_sample(stock=30)]
    orders = [_order("S-001", 500, OrderStatus.RESERVED)]
    service = MonitoringService(FakeSampleRepository(samples), FakeOrderRepository(orders))

    [entry] = service.stock_summary()

    assert entry["ratio"] == 0.06
    assert entry["status"] == "부족"


def test_no_pending_orders_uses_stock_over_one_as_ratio():
    samples = [_sample(stock=5)]
    service = MonitoringService(FakeSampleRepository(samples), FakeOrderRepository([]))

    [entry] = service.stock_summary()

    assert entry["ratio"] == 5.0
    assert entry["status"] == "여유"


def test_pending_demand_only_counts_reserved_and_producing():
    samples = [_sample(stock=50)]
    orders = [
        _order("S-001", 100, OrderStatus.RESERVED),
        _order("S-001", 100, OrderStatus.CONFIRMED),
        _order("S-001", 100, OrderStatus.RELEASED),
        _order("S-001", 100, OrderStatus.REJECTED),
    ]
    service = MonitoringService(FakeSampleRepository(samples), FakeOrderRepository(orders))

    [entry] = service.stock_summary()

    assert entry["ratio"] == 0.5
