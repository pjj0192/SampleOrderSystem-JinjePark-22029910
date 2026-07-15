from typing import Protocol

from app.models.order import Order
from app.models.sample import Sample
from app.repositories.sample_repository import SampleNotFoundError
from app.services.order_service import OrderService
from app.services.sample_service import SampleService


class OrderReservationView(Protocol):
    def show_menu(self) -> None: ...
    def get_menu_choice(self) -> str: ...
    def show_pending_reservations(self, count: int) -> None: ...
    def show_samples(self, samples: list[Sample]) -> None: ...
    def get_reservation_input(self) -> dict | None: ...
    def show_order(self, order: Order) -> None: ...
    def show_message(self, message: str) -> None: ...


class OrderReservationController:
    def __init__(
        self, service: OrderService, sample_service: SampleService, view: OrderReservationView
    ) -> None:
        self._service = service
        self._sample_service = sample_service
        self._view = view

    def handle_status(self) -> None:
        self._view.show_samples(self._sample_service.list_all())
        self._view.show_pending_reservations(len(self._service.list_reserved()))

    def handle_reserve(self) -> None:
        data = self._view.get_reservation_input()
        if data is None:
            self._view.show_message("주문을 취소했습니다.")
            return
        try:
            order = self._service.reserve(**data)
        except (ValueError, SampleNotFoundError) as error:
            self._view.show_message(f"예약 실패: {error}")
            return
        self._view.show_order(order)

    def run(self) -> None:
        self.handle_status()
        while True:
            self._view.show_menu()
            choice = self._view.get_menu_choice()
            if choice == "0":
                return
            if choice == "1":
                self.handle_reserve()
                continue
            self._view.show_message("잘못된 선택입니다.")
