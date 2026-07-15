from typing import Protocol

from app.models.production_job import ProductionJob
from app.services.order_service import OrderService
from app.services.production_service import ProductionService
from app.services.sample_service import SampleService


class ProductionView(Protocol):
    def show_menu(self) -> None: ...
    def get_menu_choice(self) -> str: ...
    def show_current_and_queue(
        self, current: ProductionJob | None, waiting: list[ProductionJob], detail: dict | None
    ) -> None: ...
    def show_in_progress(self, current: ProductionJob) -> None: ...
    def show_message(self, message: str) -> None: ...


class ProductionController:
    def __init__(
        self,
        order_service: OrderService,
        production_service: ProductionService,
        sample_service: SampleService,
        view: ProductionView,
    ) -> None:
        self._order_service = order_service
        self._production_service = production_service
        self._sample_service = sample_service
        self._view = view

    def handle_view(self) -> None:
        self._drain_completed_jobs()
        current, waiting = self._production_service.current_and_queue()
        self._view.show_current_and_queue(current, waiting, self._build_detail(current))

    def _drain_completed_jobs(self) -> None:
        """Auto-completes every job whose real elapsed time is already up
        (PRODUCING -> CONFIRMED) so viewing this screen always reflects
        current reality, instead of requiring an explicit 'generate
        completion' click for a job that already finished."""
        while self._order_service.complete_production() is not None:
            pass

    def _build_detail(self, current: ProductionJob | None) -> dict | None:
        if current is None:
            return None
        order = self._order_service.get_order(current.order_id)
        sample = self._sample_service.get(current.sample_id)
        remaining_minutes = max(current.total_time * (1 - current.progress), 0.0)
        remaining_seconds = remaining_minutes * self._production_service.minute_duration_seconds
        return {
            "quantity": order.quantity,
            "stock": sample.stock,
            "remaining_seconds": round(remaining_seconds),
        }

    def handle_advance(self) -> None:
        completed = self._order_service.complete_production()
        if completed is not None:
            self._view.show_message(f"생산 완료: {completed.order_id} -> CONFIRMED")
            return

        current, _ = self._production_service.current_and_queue()
        if current is None:
            self._view.show_message("대기 중인 생산 작업이 없습니다.")
        else:
            self._view.show_in_progress(current)

    def run(self) -> None:
        actions = {
            "1": self.handle_view,
            "2": self.handle_advance,
        }
        self.handle_view()
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
