from typing import Protocol

from app.models.production_job import ProductionJob
from app.services.order_service import OrderService
from app.services.production_service import ProductionService


class ProductionView(Protocol):
    def show_menu(self) -> None: ...
    def get_menu_choice(self) -> str: ...
    def show_current_and_queue(
        self, current: ProductionJob | None, waiting: list[ProductionJob]
    ) -> None: ...
    def show_message(self, message: str) -> None: ...


class ProductionController:
    def __init__(
        self, order_service: OrderService, production_service: ProductionService, view: ProductionView
    ) -> None:
        self._order_service = order_service
        self._production_service = production_service
        self._view = view

    def handle_view(self) -> None:
        current, waiting = self._production_service.current_and_queue()
        self._view.show_current_and_queue(current, waiting)

    def handle_advance(self) -> None:
        completed = self._order_service.complete_production()
        if completed is None:
            self._view.show_message("대기 중인 생산 작업이 없습니다.")
            return
        self._view.show_message(f"생산 완료: {completed.order_id} -> CONFIRMED")

    def run(self) -> None:
        actions = {
            "1": self.handle_view,
            "2": self.handle_advance,
        }
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
