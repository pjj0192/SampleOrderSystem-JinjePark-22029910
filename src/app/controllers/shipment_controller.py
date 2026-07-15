from typing import Protocol

from app.controllers.order_lookup import resolve_order_id
from app.models.order import Order
from app.services.order_service import InvalidOrderStateError, OrderService


class ShipmentView(Protocol):
    def show_menu(self) -> None: ...
    def get_menu_choice(self) -> str: ...
    def show_confirmed_orders(self, orders: list[Order]) -> None: ...
    def get_order_id_to_ship(self) -> str | None: ...
    def show_order(self, order: Order) -> None: ...
    def show_message(self, message: str) -> None: ...


class ShipmentController:
    def __init__(self, service: OrderService, view: ShipmentView) -> None:
        self._service = service
        self._view = view

    def handle_list(self) -> None:
        self._view.show_confirmed_orders(self._service.list_confirmed())

    def handle_ship(self) -> None:
        raw_order_id = self._view.get_order_id_to_ship()
        if raw_order_id is None:
            self._view.show_message("출고 처리를 취소했습니다.")
            return
        order_id = resolve_order_id(raw_order_id, self._service.list_confirmed())
        if order_id is None:
            self._view.show_message(f"'{raw_order_id}'에 해당하는 주문을 찾을 수 없습니다.")
            return

        try:
            order = self._service.ship(order_id)
        except InvalidOrderStateError as error:
            self._view.show_message(f"출고 실패: {error}")
            return
        self._view.show_order(order)

    def run(self) -> None:
        actions = {
            "1": self.handle_list,
            "2": self.handle_ship,
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
