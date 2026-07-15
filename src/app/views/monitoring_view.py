class ConsoleMonitoringView:
    def show_menu(self) -> None:
        print("-" * 40)
        print("[1] 주문량 확인  [2] 재고량 확인  [0] 뒤로")

    def get_menu_choice(self) -> str:
        return input("선택 > ").strip()

    def show_order_status_summary(self, summary: dict) -> None:
        print("상태별 주문 현황")
        for status, count in summary.items():
            print(f"{status:<12}{count}건")

    def show_stock_summary(self, entries: list[dict]) -> None:
        if not entries:
            print("등록된 시료가 없습니다.")
            return
        print(f"{'시료명':<20}{'재고':<8}{'상태':<6}{'잔여율'}")
        for entry in entries:
            print(
                f"{entry['name']:<20}{entry['stock']:<8}{entry['status']:<6}"
                f"{entry['ratio'] * 100:.0f}%"
            )

    def show_message(self, message: str) -> None:
        print(message)
