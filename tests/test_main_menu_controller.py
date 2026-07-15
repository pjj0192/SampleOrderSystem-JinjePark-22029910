from datetime import datetime

from app.controllers.main_menu_controller import MainMenuController
from app.models.sample import Sample
from app.repositories.order_repository import JsonOrderRepository
from app.repositories.sample_repository import JsonSampleRepository
from app.services.order_service import OrderService
from app.services.production_service import ProductionService
from app.services.sample_service import SampleService

FIXED_NOW = datetime(2026, 4, 16, 9, 0, 0)


class FakeSubController:
    def __init__(self):
        self.run_called = False

    def run(self) -> None:
        self.run_called = True


class FakeView:
    def __init__(self, menu_choices):
        self._menu_choices = list(menu_choices)
        self.shown_summaries: list[dict] = []
        self.messages: list[str] = []

    def show_summary_and_menu(self, summary: dict) -> None:
        self.shown_summaries.append(summary)

    def get_menu_choice(self) -> str:
        return self._menu_choices.pop(0)

    def show_message(self, message: str) -> None:
        self.messages.append(message)


def make_controller(tmp_path, menu_choices):
    sample_repository = JsonSampleRepository(tmp_path / "samples.json")
    sample_repository.create(
        Sample(sample_id="S-001", name="시료", avg_production_time=0.5, yield_rate=0.9, stock=100)
    )
    sample_repository.create(
        Sample(sample_id="S-002", name="시료2", avg_production_time=0.5, yield_rate=0.9, stock=50)
    )
    order_repository = JsonOrderRepository(tmp_path / "orders.json")
    production_service = ProductionService(clock=lambda: FIXED_NOW)
    order_service = OrderService(
        order_repository, sample_repository, production_service, clock=lambda: FIXED_NOW
    )
    sample_service = SampleService(sample_repository)

    sub_controllers = {
        "sample": FakeSubController(),
        "reservation": FakeSubController(),
        "approval": FakeSubController(),
        "monitoring": FakeSubController(),
        "production": FakeSubController(),
        "shipment": FakeSubController(),
    }
    view = FakeView(menu_choices)
    controller = MainMenuController(
        sample_service=sample_service,
        order_service=order_service,
        production_service=production_service,
        sample_controller=sub_controllers["sample"],
        order_reservation_controller=sub_controllers["reservation"],
        order_approval_controller=sub_controllers["approval"],
        monitoring_controller=sub_controllers["monitoring"],
        production_controller=sub_controllers["production"],
        shipment_controller=sub_controllers["shipment"],
        view=view,
        clock=lambda: FIXED_NOW,
    )
    return controller, sub_controllers, view, order_service


def test_summary_reports_sample_count_and_total_stock(tmp_path):
    controller, _, view, order_service = make_controller(tmp_path, menu_choices=["0"])

    controller.run()

    summary = view.shown_summaries[0]
    assert summary["sample_count"] == 2
    assert summary["total_stock"] == 150


def test_summary_reports_total_orders_and_production_queue_length(tmp_path):
    controller, _, view, order_service = make_controller(tmp_path, menu_choices=["0"])

    controller.run()

    summary = view.shown_summaries[0]
    assert summary["total_orders"] == 0
    assert summary["production_queue_length"] == 0


def test_choice_1_routes_to_sample_controller(tmp_path):
    controller, subs, _, _os = make_controller(tmp_path, menu_choices=["1", "0"])

    controller.run()

    assert subs["sample"].run_called


def test_choice_6_routes_to_shipment_controller(tmp_path):
    controller, subs, _, _os = make_controller(tmp_path, menu_choices=["6", "0"])

    controller.run()

    assert subs["shipment"].run_called


def test_choice_0_exits_without_routing_anywhere(tmp_path):
    controller, subs, _, _os = make_controller(tmp_path, menu_choices=["0"])

    controller.run()

    assert not any(sub.run_called for sub in subs.values())


def test_unknown_choice_shows_error_message(tmp_path):
    controller, _, view, _os = make_controller(tmp_path, menu_choices=["9", "0"])

    controller.run()

    assert any("잘못된" in m for m in view.messages)


def test_summary_reports_current_time(tmp_path):
    controller, _, view, _os = make_controller(tmp_path, menu_choices=["0"])

    controller.run()

    assert view.shown_summaries[0]["current_time"] == "2026-04-16 09:00:00"


def test_summary_reports_pending_task_counts(tmp_path):
    controller, _, view, order_service = make_controller(tmp_path, menu_choices=["0"])
    reserved = order_service.reserve(sample_id="S-001", customer_name="A", quantity=10)
    to_confirm = order_service.reserve(sample_id="S-001", customer_name="B", quantity=10)
    order_service.approve(to_confirm.order_id)

    controller.run()

    tasks = {task["label"]: task["count"] for task in view.shown_summaries[0]["pending_tasks"]}
    assert tasks["승인 대기"] == 1
    assert tasks["출고 대기"] == 1
