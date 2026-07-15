from app.models.order import Order, OrderStatus
from app.services.production_service import ProductionEstimate
from app.views.console_format import render_table, section_title
from app.views.input_helpers import InputCancelled, prompt_choice, prompt_nonblank_str_or_cancel

COLUMN_WIDTHS = (6, 20, 16, 10, 8)


class ConsoleOrderApprovalView:
    def show_menu(self) -> None:
        print()
        for line in section_title("주문 승인/거절"):
            print(line)
        print("  [1] 접수된 주문 목록   [2] 주문 승인/거절   [0] 뒤로")

    def get_menu_choice(self) -> str:
        return input("선택 > ").strip()

    def show_reserved_orders(self, orders: list[Order]) -> None:
        print()
        if not orders:
            print("승인 대기 중인 주문이 없습니다.")
            return
        rows = [
            (index, order.order_id, order.customer_name, order.sample_id, f"{order.quantity}ea")
            for index, order in enumerate(orders, start=1)
        ]
        for line in render_table(("번호", "주문번호", "고객", "시료", "수량"), rows, COLUMN_WIDTHS):
            print(line)

    def get_order_id_to_process(self) -> str | None:
        try:
            return prompt_nonblank_str_or_cancel(
                "처리할 주문 (번호, 끝자리, 또는 전체 주문번호, 0=취소) > "
            )
        except InputCancelled:
            return None

    def show_order_preview(self, order: Order, stock: int, estimate: ProductionEstimate) -> None:
        print()
        print(f"주문번호 {order.order_id}  ({order.sample_id})  주문량 {order.quantity}ea")
        print(f"  현재 재고 {stock}ea")
        if estimate.shortage == 0:
            print("  재고 충분 -> 생산 없이 즉시 승인 가능")
        else:
            print(
                f"  부족분 {estimate.shortage}ea  실생산량(예상) {estimate.actual_quantity}ea  "
                f"예상 생산시간 {estimate.total_time:.1f}분"
            )

    def get_approve_or_reject_decision(self) -> str:
        return prompt_choice("[Y] 승인  [N] 거절 > ", {"Y", "N"})

    def show_order_transition(self, previous_status: OrderStatus, order: Order) -> None:
        print()
        print(
            f"처리 완료. 주문번호 {order.order_id}  상태 변경: "
            f"{previous_status.value} -> {order.status.value}"
        )

    def show_message(self, message: str) -> None:
        print(message)
