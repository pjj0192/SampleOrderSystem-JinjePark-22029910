from datetime import datetime, timedelta
from itertools import chain, repeat
from unittest.mock import Mock

from app.controllers.production_controller import ProductionController
from app.models.order import OrderStatus
from app.models.sample import Sample
from app.repositories.order_repository import JsonOrderRepository
from app.repositories.sample_repository import JsonSampleRepository
from app.services.order_service import OrderService
from app.services.production_service import ProductionService
from app.services.sample_service import SampleService

FIXED_NOW = datetime(2026, 4, 16, 9, 0, 0)


class FakeView:
    def __init__(self, menu_choices=None):
        self._menu_choices = list(menu_choices or [])
        self.messages: list[str] = []
        self.shown_states: list[tuple] = []
        self.shown_details: list = []
        self.shown_in_progress: list = []
        self.menu_shown_count = 0

    def show_menu(self) -> None:
        self.menu_shown_count += 1

    def get_menu_choice(self) -> str:
        return self._menu_choices.pop(0)

    def show_current_and_queue(self, current, waiting, detail=None) -> None:
        self.shown_states.append((current, list(waiting)))
        self.shown_details.append(detail)

    def show_in_progress(self, current) -> None:
        self.shown_in_progress.append(current)

    def show_message(self, message: str) -> None:
        self.messages.append(message)


def _finished_clock():
    """Enqueue sees FIXED_NOW; every clock() call after that sees a time far
    enough in the future that the job reads as complete (minute_duration_
    seconds=1 test mode). Using an unbounded repeat() means it doesn't
    matter how many times advance()/current_and_queue() call the clock."""
    return Mock(side_effect=chain([FIXED_NOW], repeat(FIXED_NOW + timedelta(seconds=100_000))))


def _in_progress_clock():
    """Enqueue sees FIXED_NOW; every later call sees only 1 elapsed second
    -- nowhere near total_time (10 minutes for a 16-unit/0.8-yield order),
    so the job never reads as complete."""
    return Mock(side_effect=chain([FIXED_NOW], repeat(FIXED_NOW + timedelta(seconds=1))))


def make_controller(tmp_path, stock=0, yield_rate=0.8, clock=None, **view_kwargs):
    sample_repository = JsonSampleRepository(tmp_path / "samples.json")
    sample_repository.create(
        Sample(sample_id="S-001", name="시료", avg_production_time=0.5, yield_rate=yield_rate, stock=stock)
    )
    order_repository = JsonOrderRepository(tmp_path / "orders.json")
    production_service = ProductionService(
        clock=clock or _finished_clock(), minute_duration_seconds=1
    )
    order_service = OrderService(
        order_repository, sample_repository, production_service, clock=lambda: FIXED_NOW
    )
    sample_service = SampleService(sample_repository)
    view = FakeView(**view_kwargs)
    controller = ProductionController(order_service, production_service, sample_service, view)
    return controller, order_service, order_repository, view


def test_handle_view_shows_current_and_queue(tmp_path):
    controller, order_service, _, view = make_controller(tmp_path, clock=_in_progress_clock())
    order = order_service.reserve(sample_id="S-001", customer_name="고객", quantity=16)
    order_service.approve(order.order_id)

    controller.handle_view()

    current, waiting = view.shown_states[0]
    assert current.order_id == order.order_id
    assert waiting == []


def test_handle_view_auto_completes_job_whose_time_already_elapsed(tmp_path):
    """Viewing the screen should reflect current reality on its own --
    the user shouldn't have to separately trigger '생산 완료 처리' for a
    job that's already finished."""
    controller, order_service, order_repository, view = make_controller(tmp_path)
    order = order_service.reserve(sample_id="S-001", customer_name="고객", quantity=16)
    order_service.approve(order.order_id)

    controller.handle_view()

    assert order_repository.get(order.order_id).status == OrderStatus.CONFIRMED
    current, waiting = view.shown_states[0]
    assert current is None
    assert waiting == []


def test_handle_view_shows_order_quantity_and_stock_detail(tmp_path):
    controller, order_service, _, view = make_controller(tmp_path, stock=0, clock=_in_progress_clock())
    order = order_service.reserve(sample_id="S-001", customer_name="고객", quantity=16)
    order_service.approve(order.order_id)

    controller.handle_view()

    detail = view.shown_details[0]
    assert detail["quantity"] == 16
    assert detail["stock"] == 0
    # total_time = 0.5 * ceil(16/0.8) = 10.0 min; 1s elapsed at minute_duration_seconds=1
    # -> progress = 1/10 = 0.1 -> remaining = 10.0 * 0.9 min = 9.0 "minutes";
    # minute_duration_seconds=1 in this test config -> remaining_seconds = 9.0 * 1
    assert detail["remaining_seconds"] == 9


def test_handle_advance_completes_current_job(tmp_path):
    controller, order_service, order_repository, view = make_controller(tmp_path)
    order = order_service.reserve(sample_id="S-001", customer_name="고객", quantity=16)
    order_service.approve(order.order_id)

    controller.handle_advance()

    assert order_repository.get(order.order_id).status == OrderStatus.CONFIRMED
    assert len(view.messages) == 1


def test_handle_advance_not_yet_complete_shows_progress_message(tmp_path):
    controller, order_service, order_repository, view = make_controller(
        tmp_path, clock=_in_progress_clock()
    )
    order = order_service.reserve(sample_id="S-001", customer_name="고객", quantity=16)
    order_service.approve(order.order_id)

    controller.handle_advance()

    assert order_repository.get(order.order_id).status == OrderStatus.PRODUCING
    assert view.shown_in_progress[0].order_id == order.order_id


def test_handle_advance_with_empty_queue_shows_message(tmp_path):
    controller, _, _, view = make_controller(tmp_path)

    controller.handle_advance()

    assert any("없습니다" in m for m in view.messages)


def test_run_shows_error_message_for_unknown_choice(tmp_path):
    controller, _, _, view = make_controller(tmp_path, menu_choices=["9", "0"])

    controller.run()

    assert any("잘못된" in m for m in view.messages)


def test_run_shows_current_and_queue_by_default_on_entry(tmp_path):
    controller, order_service, _, view = make_controller(
        tmp_path, menu_choices=["0"], clock=_in_progress_clock()
    )
    order = order_service.reserve(sample_id="S-001", customer_name="고객", quantity=16)
    order_service.approve(order.order_id)

    controller.run()

    current, waiting = view.shown_states[0]
    assert current.order_id == order.order_id
    assert waiting == []
