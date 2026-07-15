from datetime import datetime

import pytest

from app.models.order import Order, OrderStatus


def make_order(**overrides):
    fields = {
        "order_id": "ORD-0001",
        "sample_id": "S-001",
        "customer_name": "삼성전자 파운드리",
        "quantity": 10,
        "status": OrderStatus.RESERVED,
        "created_at": datetime(2026, 4, 16, 9, 0, 0),
        "updated_at": datetime(2026, 4, 16, 9, 0, 0),
    }
    fields.update(overrides)
    return Order(**fields)


def test_creates_order_with_valid_fields():
    order = make_order()

    assert order.order_id == "ORD-0001"
    assert order.status == OrderStatus.RESERVED
    assert order.quantity == 10


def test_rejects_blank_order_id():
    with pytest.raises(ValueError):
        make_order(order_id="  ")


def test_rejects_blank_sample_id():
    with pytest.raises(ValueError):
        make_order(sample_id="")


def test_rejects_blank_customer_name():
    with pytest.raises(ValueError):
        make_order(customer_name="  ")


def test_rejects_non_positive_quantity():
    with pytest.raises(ValueError):
        make_order(quantity=0)


def test_order_status_enum_has_expected_members():
    assert {status.value for status in OrderStatus} == {
        "RESERVED",
        "REJECTED",
        "PRODUCING",
        "CONFIRMED",
        "RELEASED",
    }
