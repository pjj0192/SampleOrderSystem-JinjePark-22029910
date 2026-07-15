from datetime import datetime

from app.controllers.shipment_controller import ShipmentController
from app.models.order import OrderStatus
from app.models.sample import Sample
from app.repositories.order_repository import JsonOrderRepository
from app.repositories.sample_repository import JsonSampleRepository
from app.services.order_service import OrderService
from app.services.production_service import ProductionService

FIXED_NOW = datetime(2026, 4, 16, 9, 0, 0)


class FakeView:
    def __init__(self, menu_choices=None, order_id_inputs=None):
        self._menu_choices = list(menu_choices or [])
        self._order_id_inputs = list(order_id_inputs or [])
        self.messages: list[str] = []
        self.shown_order_lists: list[list] = []
        self.shown_orders: list = []
        self.menu_shown_count = 0

    def show_menu(self) -> None:
        self.menu_shown_count += 1

    def get_menu_choice(self) -> str:
        return self._menu_choices.pop(0)

    def show_confirmed_orders(self, orders) -> None:
        self.shown_order_lists.append(list(orders))

    def get_order_id_to_ship(self) -> str:
        return self._order_id_inputs.pop(0)

    def show_order(self, order) -> None:
        self.shown_orders.append(order)

    def show_message(self, message: str) -> None:
        self.messages.append(message)


def make_controller(tmp_path, **view_kwargs):
    sample_repository = JsonSampleRepository(tmp_path / "samples.json")
    sample_repository.create(
        Sample(sample_id="S-001", name="시료", avg_production_time=0.5, yield_rate=0.9, stock=300)
    )
    order_repository = JsonOrderRepository(tmp_path / "orders.json")
    production_service = ProductionService(clock=lambda: FIXED_NOW)
    service = OrderService(
        order_repository, sample_repository, production_service, clock=lambda: FIXED_NOW
    )
    view = FakeView(**view_kwargs)
    return ShipmentController(service, view), service, view


def test_handle_list_shows_only_confirmed_orders(tmp_path):
    controller, service, view = make_controller(tmp_path)
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)
    service.approve(order.order_id)

    controller.handle_list()

    assert [o.order_id for o in view.shown_order_lists[0]] == [order.order_id]


def test_handle_ship_transitions_to_released(tmp_path):
    controller, service, view = make_controller(tmp_path, order_id_inputs=[])
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)
    service.approve(order.order_id)
    view._order_id_inputs.append(order.order_id)

    controller.handle_ship()

    assert view.shown_orders[0].status == OrderStatus.RELEASED


def test_handle_ship_invalid_state_shows_error_not_raises(tmp_path):
    controller, service, view = make_controller(tmp_path, order_id_inputs=[])
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)  # still RESERVED
    view._order_id_inputs.append(order.order_id)

    controller.handle_ship()

    assert view.shown_orders == []
    assert len(view.messages) == 1


def test_run_shows_confirmed_orders_by_default_on_entry(tmp_path):
    controller, service, view = make_controller(tmp_path, menu_choices=["0"])
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)
    service.approve(order.order_id)

    controller.run()

    assert [o.order_id for o in view.shown_order_lists[0]] == [order.order_id]


def test_run_dispatches_list_then_ship_then_exit(tmp_path):
    controller, service, view = make_controller(tmp_path, menu_choices=["1", "2", "0"])
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)
    service.approve(order.order_id)
    view._order_id_inputs.append(order.order_id)

    controller.run()

    assert view.menu_shown_count == 3
    assert view.shown_orders[0].status == OrderStatus.RELEASED


def test_run_shows_error_message_for_unknown_choice(tmp_path):
    controller, _, view = make_controller(tmp_path, menu_choices=["9", "0"])

    controller.run()

    assert any("잘못된" in m for m in view.messages)


def test_handle_ship_accepts_1_based_index_into_confirmed_list(tmp_path):
    controller, service, view = make_controller(tmp_path, order_id_inputs=["2"])
    first = service.reserve(sample_id="S-001", customer_name="A", quantity=10)
    second = service.reserve(sample_id="S-001", customer_name="B", quantity=10)
    service.approve(first.order_id)
    service.approve(second.order_id)

    controller.handle_ship()

    assert view.shown_orders[0].order_id == second.order_id


def test_handle_ship_accepts_unique_order_id_suffix(tmp_path):
    controller, service, view = make_controller(tmp_path)
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)
    service.approve(order.order_id)
    view._order_id_inputs.append(order.order_id[-4:])

    controller.handle_ship()

    assert view.shown_orders[0].order_id == order.order_id


def test_handle_ship_unresolvable_input_shows_error_not_raises(tmp_path):
    controller, service, view = make_controller(tmp_path, order_id_inputs=["nonexistent"])
    order = service.reserve(sample_id="S-001", customer_name="고객", quantity=10)
    service.approve(order.order_id)

    controller.handle_ship()

    assert view.shown_orders == []
    assert len(view.messages) == 1
