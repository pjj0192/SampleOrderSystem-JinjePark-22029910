from app.models.order import Order
from app.views.input_helpers import prompt_int, prompt_nonblank_str


class ConsoleOrderReservationView:
    def show_menu(self) -> None:
        print("-" * 40)
        print("[1] 시료 주문  [0] 뒤로")

    def get_menu_choice(self) -> str:
        return input("선택 > ").strip()

    def get_reservation_input(self) -> dict:
        sample_id = prompt_nonblank_str("시료 ID > ")
        customer_name = prompt_nonblank_str("고객명 > ")
        quantity = prompt_int("주문 수량 > ", min_value=1)
        return {"sample_id": sample_id, "customer_name": customer_name, "quantity": quantity}

    def show_order(self, order: Order) -> None:
        print(f"예약 접수 완료. 주문번호 {order.order_id}  현재 상태 {order.status.value}")

    def show_message(self, message: str) -> None:
        print(message)
