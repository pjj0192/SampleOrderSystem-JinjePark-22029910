from typing import Protocol

from app.services.monitoring_service import MonitoringService


class MonitoringView(Protocol):
    """Interface the controller depends on. The real console view and the
    tests' FakeView both satisfy this shape, so the controller never
    references a concrete console implementation."""

    def show_menu(self) -> None: ...
    def get_menu_choice(self) -> str: ...
    def show_order_status_summary(self, summary: dict) -> None: ...
    def show_stock_summary(self, entries: list[dict]) -> None: ...
    def show_message(self, message: str) -> None: ...


class MonitoringController:
    def __init__(self, service: MonitoringService, view: MonitoringView) -> None:
        self._service = service
        self._view = view

    def handle_order_status(self) -> None:
        self._view.show_order_status_summary(self._service.order_status_summary())

    def handle_stock(self) -> None:
        self._view.show_stock_summary(self._service.stock_summary())

    def run(self) -> None:
        actions = {
            "1": self.handle_order_status,
            "2": self.handle_stock,
        }
        self.handle_order_status()
        self.handle_stock()
        while True:
            self._view.show_menu()
            choice = self._view.get_menu_choice()
            if choice == "0":
                return
            action = actions.get(choice)
            if action is None:
                self._view.show_message("잘못된 선택입니다.")
                continue
            action()
