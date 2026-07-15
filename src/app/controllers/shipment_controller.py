from typing import Protocol

from app.models.order import Order
from app.services.order_service import InvalidOrderStateError, OrderService


class ShipmentView(Protocol):
    def show_menu(self) -> None: ...
    def get_menu_choice(self) -> str: ...
    def show_confirmed_orders(self, orders: list[Order]) -> None: ...
    def get_order_id_to_ship(self) -> str: ...
    def show_order(self, order: Order) -> None: ...
    def show_message(self, message: str) -> None: ...


class ShipmentController:
    def __init__(self, service: OrderService, view: ShipmentView) -> None:
        self._service = service
        self._view = view

    def handle_list(self) -> None:
        self._view.show_confirmed_orders(self._service.list_confirmed())

    def handle_ship(self) -> None:
        order_id = self._view.get_order_id_to_ship()
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
