from typing import Protocol

from app.models.order import Order
from app.repositories.sample_repository import SampleNotFoundError
from app.services.order_service import OrderService


class OrderReservationView(Protocol):
    def show_menu(self) -> None: ...
    def get_menu_choice(self) -> str: ...
    def get_reservation_input(self) -> dict: ...
    def show_order(self, order: Order) -> None: ...
    def show_message(self, message: str) -> None: ...


class OrderReservationController:
    def __init__(self, service: OrderService, view: OrderReservationView) -> None:
        self._service = service
        self._view = view

    def handle_reserve(self) -> None:
        data = self._view.get_reservation_input()
        try:
            order = self._service.reserve(**data)
        except (ValueError, SampleNotFoundError) as error:
            self._view.show_message(f"예약 실패: {error}")
            return
        self._view.show_order(order)

    def run(self) -> None:
        while True:
            self._view.show_menu()
            choice = self._view.get_menu_choice()
            if choice == "0":
                return
            if choice == "1":
                self.handle_reserve()
                continue
            self._view.show_message("잘못된 선택입니다.")
