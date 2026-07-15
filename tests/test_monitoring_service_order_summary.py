from datetime import datetime

from app.models.order import Order, OrderStatus
from app.services.monitoring_service import MonitoringService

FIXED_NOW = datetime(2026, 4, 16, 9, 0, 0)


class FakeOrderRepository:
    def __init__(self, orders: list[Order]) -> None:
        self._orders = orders

    def list_all(self) -> list[Order]:
        return self._orders

    def list_by_sample(self, sample_id: str) -> list[Order]:
        return [o for o in self._orders if o.sample_id == sample_id]


class FakeSampleRepository:
    def list_all(self):
        return []

    def get(self, sample_id: str):
        return None


def _order(order_id, status, sample_id="S-001", quantity=1):
    return Order(
        order_id=order_id,
        sample_id=sample_id,
        customer_name="고객",
        quantity=quantity,
        status=status,
        created_at=FIXED_NOW,
        updated_at=FIXED_NOW,
    )


def test_counts_orders_by_status():
    orders = [
        _order("ORD-1", OrderStatus.RESERVED),
        _order("ORD-2", OrderStatus.RESERVED),
        _order("ORD-3", OrderStatus.CONFIRMED),
        _order("ORD-4", OrderStatus.PRODUCING),
        _order("ORD-5", OrderStatus.RELEASED),
    ]
    service = MonitoringService(FakeSampleRepository(), FakeOrderRepository(orders))

    summary = service.order_status_summary()

    assert summary == {
        "RESERVED": 2,
        "CONFIRMED": 1,
        "PRODUCING": 1,
        "RELEASED": 1,
    }


def test_excludes_rejected_orders_from_summary():
    orders = [
        _order("ORD-1", OrderStatus.RESERVED),
        _order("ORD-2", OrderStatus.REJECTED),
        _order("ORD-3", OrderStatus.REJECTED),
    ]
    service = MonitoringService(FakeSampleRepository(), FakeOrderRepository(orders))

    summary = service.order_status_summary()

    assert "REJECTED" not in summary
    assert summary["RESERVED"] == 1


def test_returns_zero_counts_when_no_orders():
    service = MonitoringService(FakeSampleRepository(), FakeOrderRepository([]))

    summary = service.order_status_summary()

    assert summary == {
        "RESERVED": 0,
        "CONFIRMED": 0,
        "PRODUCING": 0,
        "RELEASED": 0,
    }
