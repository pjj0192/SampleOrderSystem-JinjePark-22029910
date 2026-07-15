from datetime import datetime

from app.controllers.production_controller import ProductionController
from app.models.order import OrderStatus
from app.models.sample import Sample
from app.repositories.order_repository import JsonOrderRepository
from app.repositories.sample_repository import JsonSampleRepository
from app.services.order_service import OrderService
from app.services.production_service import ProductionService

FIXED_NOW = datetime(2026, 4, 16, 9, 0, 0)


class FakeView:
    def __init__(self, menu_choices=None):
        self._menu_choices = list(menu_choices or [])
        self.messages: list[str] = []
        self.shown_states: list[tuple] = []
        self.menu_shown_count = 0

    def show_menu(self) -> None:
        self.menu_shown_count += 1

    def get_menu_choice(self) -> str:
        return self._menu_choices.pop(0)

    def show_current_and_queue(self, current, waiting) -> None:
        self.shown_states.append((current, list(waiting)))

    def show_message(self, message: str) -> None:
        self.messages.append(message)


def make_controller(tmp_path, stock=0, yield_rate=0.8, **view_kwargs):
    sample_repository = JsonSampleRepository(tmp_path / "samples.json")
    sample_repository.create(
        Sample(sample_id="S-001", name="시료", avg_production_time=0.5, yield_rate=yield_rate, stock=stock)
    )
    order_repository = JsonOrderRepository(tmp_path / "orders.json")
    production_service = ProductionService(clock=lambda: FIXED_NOW)
    order_service = OrderService(
        order_repository, sample_repository, production_service, clock=lambda: FIXED_NOW
    )
    view = FakeView(**view_kwargs)
    controller = ProductionController(order_service, production_service, view)
    return controller, order_service, order_repository, view


def test_handle_view_shows_current_and_queue(tmp_path):
    controller, order_service, _, view = make_controller(tmp_path)
    order = order_service.reserve(sample_id="S-001", customer_name="고객", quantity=16)
    order_service.approve(order.order_id)

    controller.handle_view()

    current, waiting = view.shown_states[0]
    assert current.order_id == order.order_id
    assert waiting == []


def test_handle_advance_completes_current_job(tmp_path):
    controller, order_service, order_repository, view = make_controller(tmp_path)
    order = order_service.reserve(sample_id="S-001", customer_name="고객", quantity=16)
    order_service.approve(order.order_id)

    controller.handle_advance()

    assert order_repository.get(order.order_id).status == OrderStatus.CONFIRMED
    assert len(view.messages) == 1


def test_handle_advance_with_empty_queue_shows_message(tmp_path):
    controller, _, _, view = make_controller(tmp_path)

    controller.handle_advance()

    assert any("없습니다" in m for m in view.messages)


def test_run_shows_error_message_for_unknown_choice(tmp_path):
    controller, _, _, view = make_controller(tmp_path, menu_choices=["9", "0"])

    controller.run()

    assert any("잘못된" in m for m in view.messages)
