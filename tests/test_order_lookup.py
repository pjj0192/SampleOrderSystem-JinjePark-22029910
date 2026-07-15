from datetime import datetime

from app.controllers.order_lookup import resolve_order_id
from app.models.order import Order, OrderStatus

NOW = datetime(2026, 4, 16, 9, 0, 0)


def make_order(order_id):
    return Order(
        order_id=order_id,
        sample_id="S-001",
        customer_name="고객",
        quantity=10,
        status=OrderStatus.RESERVED,
        created_at=NOW,
        updated_at=NOW,
    )


CANDIDATES = [
    make_order("ORD-20260416-0001"),
    make_order("ORD-20260416-0002"),
    make_order("ORD-20260416-0003"),
]


def test_resolves_exact_order_id():
    assert resolve_order_id("ORD-20260416-0002", CANDIDATES) == "ORD-20260416-0002"


def test_resolves_1_based_index_from_displayed_list():
    assert resolve_order_id("2", CANDIDATES) == "ORD-20260416-0002"


def test_resolves_unique_suffix_match():
    assert resolve_order_id("0003", CANDIDATES) == "ORD-20260416-0003"


def test_returns_none_for_index_out_of_range():
    assert resolve_order_id("99", CANDIDATES) is None


def test_returns_none_when_no_match_found():
    assert resolve_order_id("nonexistent", CANDIDATES) is None


def test_returns_none_for_ambiguous_suffix():
    ambiguous = [make_order("ORD-20260416-0011"), make_order("ORD-20260416-0111")]
    assert resolve_order_id("11", ambiguous) is None


def test_returns_none_for_empty_candidate_list():
    assert resolve_order_id("1", []) is None
