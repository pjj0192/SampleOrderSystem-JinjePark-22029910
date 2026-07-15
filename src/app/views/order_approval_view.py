from app.models.order import Order


class ConsoleOrderApprovalView:
    def show_menu(self) -> None:
        print("-" * 40)
        print("[1] 접수된 주문 목록  [2] 주문 승인/거절  [0] 뒤로")

    def get_menu_choice(self) -> str:
        return input("선택 > ").strip()

    def show_reserved_orders(self, orders: list[Order]) -> None:
        if not orders:
            print("승인 대기 중인 주문이 없습니다.")
            return
        print(f"{'주문번호':<20}{'고객':<16}{'시료':<10}{'수량':<8}")
        for order in orders:
            print(
                f"{order.order_id:<20}{order.customer_name:<16}"
                f"{order.sample_id:<10}{order.quantity:<8}"
            )

    def get_order_id_to_process(self) -> str:
        return input("처리할 주문번호 > ").strip()

    def get_approve_or_reject_decision(self) -> str:
        return input("[Y] 승인  [N] 거절 > ").strip().upper()

    def show_order(self, order: Order) -> None:
        print(f"처리 완료. 주문번호 {order.order_id}  상태 {order.status.value}")

    def show_message(self, message: str) -> None:
        print(message)
