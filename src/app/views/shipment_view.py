from app.models.order import Order
from app.views.console_format import render_table, section_title
from app.views.input_helpers import InputCancelled, prompt_nonblank_str_or_cancel

COLUMN_WIDTHS = (6, 20, 16, 10, 8)


class ConsoleShipmentView:
    def show_menu(self) -> None:
        print()
        for line in section_title("출고 처리"):
            print(line)
        print("  [1] 출고 가능 주문 목록   [2] 출고 처리   [0] 뒤로")

    def get_menu_choice(self) -> str:
        return input("선택 > ").strip()

    def show_confirmed_orders(self, orders: list[Order]) -> None:
        print()
        if not orders:
            print("출고 가능한 주문이 없습니다.")
            return
        rows = [
            (index, order.order_id, order.customer_name, order.sample_id, f"{order.quantity}ea")
            for index, order in enumerate(orders, start=1)
        ]
        for line in render_table(("번호", "주문번호", "고객", "시료", "수량"), rows, COLUMN_WIDTHS):
            print(line)

    def get_order_id_to_ship(self) -> str | None:
        try:
            return prompt_nonblank_str_or_cancel(
                "출고할 주문 (번호, 끝자리, 또는 전체 주문번호, 0=취소) > "
            )
        except InputCancelled:
            return None

    def show_order(self, order: Order) -> None:
        print()
        print(f"출고 처리 완료. 주문번호 {order.order_id}  상태 {order.status.value}")

    def show_message(self, message: str) -> None:
        print(message)
