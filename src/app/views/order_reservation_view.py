from app.models.order import Order
from app.models.sample import Sample
from app.views.console_format import render_table, section_title
from app.views.input_helpers import (
    InputCancelled,
    prompt_int_or_cancel,
    prompt_nonblank_str_or_cancel,
)

SAMPLE_COLUMN_WIDTHS = (10, 20, 10, 8)


class ConsoleOrderReservationView:
    def show_menu(self) -> None:
        print()
        for line in section_title("시료 주문"):
            print(line)
        print("  [1] 시료 주문   [0] 뒤로")

    def get_menu_choice(self) -> str:
        return input("선택 > ").strip()

    def show_samples(self, samples: list[Sample]) -> None:
        print()
        print("주문 가능한 시료 목록")
        if not samples:
            print("등록된 시료가 없습니다.")
            return
        rows = [
            (sample.sample_id, sample.name, f"{sample.avg_production_time}분", f"{sample.stock}ea")
            for sample in samples
        ]
        for line in render_table(("ID", "이름", "생산시간", "재고"), rows, SAMPLE_COLUMN_WIDTHS):
            print(line)

    def show_pending_reservations(self, count: int) -> None:
        print()
        print(f"현재 승인 대기 중인 주문 {count}건")

    def get_reservation_input(self) -> dict | None:
        """Returns None if the user types 0 at any prompt to back out of a
        reservation they entered by mistake."""
        try:
            sample_id = prompt_nonblank_str_or_cancel("시료 ID (0=취소) > ")
            customer_name = prompt_nonblank_str_or_cancel("고객명 (0=취소) > ")
            quantity = prompt_int_or_cancel("주문 수량 (0=취소) > ", min_value=1)
        except InputCancelled:
            return None
        return {"sample_id": sample_id, "customer_name": customer_name, "quantity": quantity}

    def show_order(self, order: Order) -> None:
        print()
        print(f"예약 접수 완료. 주문번호 {order.order_id}  현재 상태 {order.status.value}")

    def show_message(self, message: str) -> None:
        print(message)
