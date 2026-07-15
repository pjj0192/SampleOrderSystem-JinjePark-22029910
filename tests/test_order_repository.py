import json
from datetime import datetime

import pytest

from app.models.order import Order, OrderStatus
from app.repositories.order_repository import (
    DuplicateOrderIdError,
    JsonOrderRepository,
    OrderNotFoundError,
)

NOW = datetime(2026, 4, 16, 9, 0, 0)


def make_order(order_id="ORD-0001", **overrides):
    fields = {
        "order_id": order_id,
        "sample_id": "S-001",
        "customer_name": "삼성전자 파운드리",
        "quantity": 10,
        "status": OrderStatus.RESERVED,
        "created_at": NOW,
        "updated_at": NOW,
    }
    fields.update(overrides)
    return Order(**fields)


def test_create_persists_to_file_and_is_readable(tmp_path):
    file_path = tmp_path / "orders.json"
    repo = JsonOrderRepository(file_path)

    repo.create(make_order())

    assert repo.get("ORD-0001").customer_name == "삼성전자 파운드리"
    raw = json.loads(file_path.read_text(encoding="utf-8"))
    assert raw == [make_order().to_dict()]


def test_list_all_returns_every_created_order(tmp_path):
    repo = JsonOrderRepository(tmp_path / "orders.json")
    repo.create(make_order("ORD-0001"))
    repo.create(make_order("ORD-0002"))

    assert {o.order_id for o in repo.list_all()} == {"ORD-0001", "ORD-0002"}


def test_get_missing_order_returns_none(tmp_path):
    repo = JsonOrderRepository(tmp_path / "orders.json")
    assert repo.get("ORD-9999") is None


def test_create_duplicate_id_raises(tmp_path):
    repo = JsonOrderRepository(tmp_path / "orders.json")
    repo.create(make_order("ORD-0001"))

    with pytest.raises(DuplicateOrderIdError):
        repo.create(make_order("ORD-0001"))


def test_update_modifies_existing_order_and_persists(tmp_path):
    file_path = tmp_path / "orders.json"
    repo = JsonOrderRepository(file_path)
    repo.create(make_order("ORD-0001", status=OrderStatus.RESERVED))

    repo.update(make_order("ORD-0001", status=OrderStatus.CONFIRMED))

    assert repo.get("ORD-0001").status == OrderStatus.CONFIRMED
    raw = json.loads(file_path.read_text(encoding="utf-8"))
    assert raw[0]["status"] == "CONFIRMED"


def test_update_missing_order_raises(tmp_path):
    repo = JsonOrderRepository(tmp_path / "orders.json")

    with pytest.raises(OrderNotFoundError):
        repo.update(make_order("ORD-9999"))


def test_list_by_sample_returns_only_matching_orders(tmp_path):
    repo = JsonOrderRepository(tmp_path / "orders.json")
    repo.create(make_order("ORD-0001", sample_id="S-001"))
    repo.create(make_order("ORD-0002", sample_id="S-002"))

    result = repo.list_by_sample("S-001")

    assert [o.order_id for o in result] == ["ORD-0001"]


def test_data_survives_repository_recreation_at_same_path(tmp_path):
    file_path = tmp_path / "orders.json"
    first_run = JsonOrderRepository(file_path)
    first_run.create(make_order("ORD-0001"))
    del first_run

    second_run = JsonOrderRepository(file_path)

    assert second_run.get("ORD-0001") is not None
