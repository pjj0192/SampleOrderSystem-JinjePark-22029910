from typing import Protocol

from app.controllers.order_lookup import resolve_order_id
from app.models.order import Order, OrderStatus
from app.services.order_service import InvalidOrderStateError, OrderService
from app.services.production_service import ProductionEstimate, ProductionService
from app.services.sample_service import SampleService


class OrderApprovalView(Protocol):
    def show_menu(self) -> None: ...
    def get_menu_choice(self) -> str: ...
    def show_reserved_orders(self, orders: list[Order]) -> None: ...
    def get_order_id_to_process(self) -> str | None: ...
    def show_order_preview(self, order: Order, stock: int, estimate: ProductionEstimate) -> None: ...
    def get_approve_or_reject_decision(self) -> str: ...
    def show_order_transition(self, previous_status: OrderStatus, order: Order) -> None: ...
    def show_message(self, message: str) -> None: ...


class OrderApprovalController:
    def __init__(
        self,
        service: OrderService,
        sample_service: SampleService,
        production_service: ProductionService,
        view: OrderApprovalView,
    ) -> None:
        self._service = service
        self._sample_service = sample_service
        self._production_service = production_service
        self._view = view

    def handle_list(self) -> None:
        self._view.show_reserved_orders(self._service.list_reserved())

    def handle_process(self) -> None:
        reserved = self._service.list_reserved()
        raw_order_id = self._view.get_order_id_to_process()
        if raw_order_id is None:
            self._view.show_message("주문 처리를 취소했습니다.")
            return
        order_id = resolve_order_id(raw_order_id, reserved)
        if order_id is None:
            self._view.show_message(f"'{raw_order_id}'에 해당하는 주문을 찾을 수 없습니다.")
            return

        order = next(o for o in reserved if o.order_id == order_id)
        sample = self._sample_service.get(order.sample_id)
        estimate = self._production_service.estimate_production(
            order.quantity, sample.stock, sample.avg_production_time, sample.yield_rate
        )
        self._view.show_order_preview(order, sample.stock, estimate)

        previous_status = order.status
        decision = self._view.get_approve_or_reject_decision()
        try:
            if decision == "Y":
                order = self._service.approve(order_id)
            else:
                order = self._service.reject(order_id)
        except InvalidOrderStateError as error:
            self._view.show_message(f"처리 실패: {error}")
            return
        self._view.show_order_transition(previous_status, order)

    def run(self) -> None:
        actions = {
            "1": self.handle_list,
            "2": self.handle_process,
        }
        self.handle_list()
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
