from datetime import datetime

from app.controllers.order_approval_controller import OrderApprovalController
from app.models.order import OrderStatus
from app.models.sample import Sample
from app.repositories.order_repository import JsonOrderRepository
from app.repositories.sample_repository import JsonSampleRepository
from app.services.order_service import OrderService
from app.services.production_service import ProductionService
from app.services.sample_service import SampleService

FIXED_NOW = datetime(2026, 4, 16, 9, 0, 0)


class FakeView:
    def __init__(self, menu_choices=None, order_id_inputs=None, decisions=None):
        self._menu_choices = list(menu_choices or [])
        self._order_id_inputs = list(order_id_inputs or [])
        self._decisions = list(decisions or [])
        self.messages: list[str] = []
        self.shown_order_lists: list[list] = []
        self.shown_previews: list = []
        self.shown_orders: list = []
        self.shown_transitions: list = []
        self.menu_shown_count = 0

    def show_menu(self) -> None:
        self.menu_shown_count += 1

    def get_menu_choice(self) -> str:
        return self._menu_choices.pop(0)

    def show_reserved_orders(self, orders) -> None:
        self.shown_order_lists.append(list(orders))

    def get_order_id_to_process(self) -> str:
        return self._order_id_inputs.pop(0)

    def show_order_preview(self, order, stock, estimate) -> None:
        self.shown_previews.append((order, stock, estimate))

    def get_approve_or_reject_decision(self) -> str:
        return self._decisions.pop(0)

    def show_order_transition(self, previous_status, order) -> None:
        self.shown_orders.append(order)
        self.shown_transitions.append((previous_status, order.status))

    def show_message(self, message: str) -> None:
        self.messages.append(message)


def make_controller(tmp_path, stock=300, **view_kwargs):
    sample_repository = JsonSampleRepository(tmp_path / "samples.json")
    sample_repository.create(
        Sample(sample_id="S-001", name="시료", avg_production_time=0.5, yield_rate=0.9, stock=stock)
    )
    order_repository = JsonOrderRepository(tmp_path / "orders.json")
    production_service = ProductionService(clock=lambda: FIXED_NOW)
    sample_service = SampleService(sample_repository)
    service = OrderService(
        order_repository, sample_repository, production_service, clock=lambda: FIXED_NOW
    )
    view = FakeView(**view_kwargs)
    return (
        OrderApprovalController(service, sample_service, production_service, view),
        service,
        view,
    )


def test_handle_list_shows_only_reserved_orders(tmp_path):
    controller, service, view = make_controller(tmp_path)
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)

    controller.handle_list()

    assert [o.order_id for o in view.shown_order_lists[0]] == [order.order_id]


def test_handle_process_shows_shortage_preview_before_decision(tmp_path):
    controller, service, view = make_controller(tmp_path, stock=4, order_id_inputs=[], decisions=["Y"])
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)
    view._order_id_inputs.append(order.order_id)

    controller.handle_process()

    shown_order, stock, estimate = view.shown_previews[0]
    assert shown_order.order_id == order.order_id
    assert stock == 4
    assert estimate.shortage == 6  # 10 - 4
    assert estimate.actual_quantity == 7  # ceil(6 / 0.9)
    assert estimate.total_time == 3.5  # 0.5 * 7


def test_handle_process_preview_shows_zero_shortage_when_stock_sufficient(tmp_path):
    controller, service, view = make_controller(tmp_path, stock=300, order_id_inputs=[], decisions=["Y"])
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)
    view._order_id_inputs.append(order.order_id)

    controller.handle_process()

    _, _, estimate = view.shown_previews[0]
    assert estimate.shortage == 0
    assert estimate.actual_quantity == 0


def test_handle_process_approve_decision_confirms_order(tmp_path):
    controller, service, view = make_controller(tmp_path, order_id_inputs=[], decisions=["Y"])
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)
    view._order_id_inputs.append(order.order_id)

    controller.handle_process()

    assert view.shown_orders[0].status == OrderStatus.CONFIRMED
    assert view.shown_transitions[0] == (OrderStatus.RESERVED, OrderStatus.CONFIRMED)


def test_handle_process_reject_decision_rejects_order(tmp_path):
    controller, service, view = make_controller(tmp_path, order_id_inputs=[], decisions=["N"])
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)
    view._order_id_inputs.append(order.order_id)

    controller.handle_process()

    assert view.shown_orders[0].status == OrderStatus.REJECTED


def test_run_shows_reserved_orders_by_default_on_entry(tmp_path):
    controller, service, view = make_controller(tmp_path, menu_choices=["0"])
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)

    controller.run()

    assert [o.order_id for o in view.shown_order_lists[0]] == [order.order_id]


def test_run_dispatches_list_then_process_then_exit(tmp_path):
    controller, service, view = make_controller(
        tmp_path, menu_choices=["1", "2", "0"], decisions=["Y"]
    )
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)
    view._order_id_inputs.append(order.order_id)

    controller.run()

    assert view.menu_shown_count == 3
    assert view.shown_orders[0].status == OrderStatus.CONFIRMED


def test_run_shows_error_message_for_unknown_choice(tmp_path):
    controller, service, view = make_controller(tmp_path, menu_choices=["9", "0"])

    controller.run()

    assert any("잘못된" in m for m in view.messages)


def test_handle_process_on_already_processed_order_shows_error_not_raises(tmp_path):
    controller, service, view = make_controller(
        tmp_path, order_id_inputs=[], decisions=["Y", "Y"]
    )
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)
    service.approve(order.order_id)  # already CONFIRMED
    view._order_id_inputs.append(order.order_id)

    controller.handle_process()

    assert view.shown_orders == []
    assert len(view.messages) == 1


def test_handle_process_accepts_1_based_index_into_reserved_list(tmp_path):
    controller, service, view = make_controller(tmp_path, order_id_inputs=["2"], decisions=["Y"])
    service.reserve(sample_id="S-001", customer_name="A", quantity=10)
    second = service.reserve(sample_id="S-001", customer_name="B", quantity=10)

    controller.handle_process()

    assert view.shown_orders[0].order_id == second.order_id


def test_handle_process_accepts_unique_order_id_suffix(tmp_path):
    controller, service, view = make_controller(tmp_path, decisions=["Y"])
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)
    suffix = order.order_id[-4:]
    view._order_id_inputs.append(suffix)

    controller.handle_process()

    assert view.shown_orders[0].order_id == order.order_id


def test_handle_process_unresolvable_input_shows_error_not_raises(tmp_path):
    controller, service, view = make_controller(tmp_path, order_id_inputs=["nonexistent"])
    service.reserve(sample_id="S-001", customer_name="고객", quantity=10)

    controller.handle_process()

    assert view.shown_orders == []
    assert len(view.messages) == 1
