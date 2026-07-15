from app.views.console_format import render_table, section_title
from app.views.progress_bar import render_progress_bar

ORDER_STATUS_COLUMN_WIDTHS = (12, 8)
STOCK_COLUMN_WIDTHS = (6, 10, 20, 8, 6, 8, 20)
STOCK_BAR_WIDTH = 12


class ConsoleMonitoringView:
    def show_menu(self) -> None:
        print()
        for line in section_title("모니터링"):
            print(line)
        print("  [1] 주문량 확인   [2] 재고량 확인   [0] 뒤로")

    def get_menu_choice(self) -> str:
        return input("선택 > ").strip()

    def show_order_status_summary(self, summary: dict) -> None:
        print()
        print("상태별 주문 현황")
        rows = [(status, f"{count}건") for status, count in summary.items()]
        for line in render_table(("상태", "건수"), rows, ORDER_STATUS_COLUMN_WIDTHS):
            print(line)

    def show_stock_summary(self, entries: list[dict]) -> None:
        print()
        print("시료별 재고 현황")
        if not entries:
            print("등록된 시료가 없습니다.")
            return
        rows = [
            (
                index,
                entry["sample_id"],
                entry["name"],
                f"{entry['stock']}ea",
                entry["status"],
                f"{self._display_ratio(entry['ratio']):.0f}%",
                render_progress_bar(self._display_ratio(entry["ratio"]) / 100, width=STOCK_BAR_WIDTH),
            )
            for index, entry in enumerate(entries, start=1)
        ]
        for line in render_table(
            ("번호", "시료ID", "시료명", "재고", "상태", "잔여율", "잔여율 바"), rows, STOCK_COLUMN_WIDTHS
        ):
            print(line)

    @staticmethod
    def _display_ratio(ratio: float) -> float:
        """Service's ratio is uncapped by design (stock / max(pending_demand, 1))
        -- with no pending demand it degenerates to the raw stock count, e.g.
        3800%. Classification (여유/부족/고갈) uses the raw value; only this
        on-screen percentage is capped at 100% for readability."""
        return min(ratio * 100, 100.0)

    def show_message(self, message: str) -> None:
        print(message)
