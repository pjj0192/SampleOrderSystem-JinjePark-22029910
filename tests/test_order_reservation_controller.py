from datetime import datetime

from app.controllers.order_reservation_controller import OrderReservationController
from app.models.sample import Sample
from app.repositories.order_repository import JsonOrderRepository
from app.repositories.sample_repository import JsonSampleRepository
from app.services.order_service import OrderService

FIXED_NOW = datetime(2026, 4, 16, 9, 0, 0)


class FakeView:
    def __init__(self, menu_choices=None, reservation_inputs=None):
        self._menu_choices = list(menu_choices or [])
        self._reservation_inputs = list(reservation_inputs or [])
        self.messages: list[str] = []
        self.shown_orders: list = []
        self.menu_shown_count = 0

    def show_menu(self) -> None:
        self.menu_shown_count += 1

    def get_menu_choice(self) -> str:
        return self._menu_choices.pop(0)

    def get_reservation_input(self) -> dict:
        return self._reservation_inputs.pop(0)

    def show_order(self, order) -> None:
        self.shown_orders.append(order)

    def show_message(self, message: str) -> None:
        self.messages.append(message)


def make_controller(tmp_path, **view_kwargs):
    sample_repository = JsonSampleRepository(tmp_path / "samples.json")
    sample_repository.create(
        Sample(sample_id="S-001", name="실리콘 웨이퍼-8인치", avg_production_time=0.5, yield_rate=0.92)
    )
    order_repository = JsonOrderRepository(tmp_path / "orders.json")
    service = OrderService(order_repository, sample_repository, clock=lambda: FIXED_NOW)
    view = FakeView(**view_kwargs)
    return OrderReservationController(service, view), order_repository, view


def test_handle_reserve_success_shows_created_order(tmp_path):
    controller, order_repository, view = make_controller(
        tmp_path,
        reservation_inputs=[
            {"sample_id": "S-001", "customer_name": "삼성전자 파운드리", "quantity": 200}
        ],
    )

    controller.handle_reserve()

    assert len(order_repository.list_all()) == 1
    assert view.shown_orders[0].quantity == 200


def test_handle_reserve_unknown_sample_shows_error_not_raises(tmp_path):
    controller, order_repository, view = make_controller(
        tmp_path,
        reservation_inputs=[{"sample_id": "S-999", "customer_name": "고객", "quantity": 10}],
    )

    controller.handle_reserve()

    assert order_repository.list_all() == []
    assert len(view.messages) == 1


def test_run_dispatches_reserve_then_exit(tmp_path):
    controller, order_repository, view = make_controller(
        tmp_path,
        menu_choices=["1", "0"],
        reservation_inputs=[{"sample_id": "S-001", "customer_name": "고객", "quantity": 10}],
    )

    controller.run()

    assert view.menu_shown_count == 2
    assert len(order_repository.list_all()) == 1


def test_run_shows_error_message_for_unknown_choice(tmp_path):
    controller, order_repository, view = make_controller(tmp_path, menu_choices=["9", "0"])

    controller.run()

    assert any("잘못된" in m for m in view.messages)
