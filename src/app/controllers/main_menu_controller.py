from collections.abc import Callable
from datetime import datetime
from typing import Protocol

from app.services.order_service import OrderService
from app.services.production_service import ProductionService
from app.services.sample_service import SampleService


class SubController(Protocol):
    def run(self) -> None: ...


class MainMenuView(Protocol):
    def show_summary_and_menu(self, summary: dict) -> None: ...
    def get_menu_choice(self) -> str: ...
    def show_message(self, message: str) -> None: ...


class MainMenuController:
    """Routes to sub-controllers only -- holds no business logic itself.
    Depends on Services (not Repositories) purely to compose the summary
    line shown above the menu."""

    def __init__(
        self,
        sample_service: SampleService,
        order_service: OrderService,
        production_service: ProductionService,
        sample_controller: SubController,
        order_reservation_controller: SubController,
        order_approval_controller: SubController,
        monitoring_controller: SubController,
        production_controller: SubController,
        shipment_controller: SubController,
        view: MainMenuView,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._sample_service = sample_service
        self._order_service = order_service
        self._production_service = production_service
        self._routes: dict[str, SubController] = {
            "1": sample_controller,
            "2": order_reservation_controller,
            "3": order_approval_controller,
            "4": monitoring_controller,
            "5": production_controller,
            "6": shipment_controller,
        }
        self._view = view
        self._clock = clock

    def _build_summary(self) -> dict:
        samples = self._sample_service.list_all()
        return {
            "current_time": self._clock().strftime("%Y-%m-%d %H:%M:%S"),
            "sample_count": len(samples),
            "total_stock": sum(sample.stock for sample in samples),
            "total_orders": self._order_service.total_order_count(),
            "production_queue_length": len(self._production_service.queue()),
            "pending_tasks": [
                {"label": "승인 대기", "count": len(self._order_service.list_reserved())},
                {"label": "출고 대기", "count": len(self._order_service.list_confirmed())},
            ],
        }

    def run(self) -> None:
        while True:
            self._view.show_summary_and_menu(self._build_summary())
            choice = self._view.get_menu_choice()
            if choice == "0":
                return
            sub_controller = self._routes.get(choice)
            if sub_controller is None:
                self._view.show_message("잘못된 선택입니다.")
                continue
            sub_controller.run()
