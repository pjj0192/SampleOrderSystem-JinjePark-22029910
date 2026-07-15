from collections.abc import Callable

from app.models.production_job import ProductionJob
from app.views.console_format import render_table, section_title
from app.views.live_refresh import clear_screen, wait_for_enter_or_timeout
from app.views.progress_bar import render_progress_bar

QUEUE_COLUMN_WIDTHS = (6, 12, 12, 10, 10, 10)
LIVE_REFRESH_SECONDS = 1.0
# Safety cap, not a UX target: on a non-interactive stdin (e.g. redirected
# input), the keypress check below never fires, so this bounds the loop
# to roughly an hour instead of refreshing forever.
LIVE_MAX_REFRESHES = 3600


class ConsoleProductionView:
    def show_menu(self) -> None:
        print()
        for line in section_title("생산라인 조회"):
            print(line)
        print(
            "  [1] 생산 현황 조회   [2] 생산 완료 처리(다음 작업)   "
            "[3] 실시간 보기   [0] 뒤로"
        )

    def get_menu_choice(self) -> str:
        return input("선택 > ").strip()

    def show_current_and_queue(
        self,
        current: ProductionJob | None,
        waiting: list[ProductionJob],
        detail: dict | None = None,
    ) -> None:
        print()
        print("현재 처리 중 (FIFO)")
        if current is None:
            print("  생산 중인 작업이 없습니다.")
        else:
            bar = render_progress_bar(current.progress)
            print(f"  주문 {current.order_id}  ({current.sample_id})")
            if detail is not None:
                print(f"  주문량 {detail['quantity']}ea  현재 재고 {detail['stock']}ea")
            print(
                f"  부족분 {current.shortage}ea  실생산량 {current.actual_quantity}ea  "
                f"총 생산시간 {current.total_time:.1f}분"
            )
            if detail is not None:
                print(f"  완료까지 남은 시간 {detail['remaining_seconds']}초")
            print(f"  진행률 {bar}")

        print()
        print(f"대기 중인 주문 (FIFO 순, {len(waiting)}건)")
        if not waiting:
            print("  대기 중인 주문이 없습니다.")
            return
        rows = [
            (
                index,
                job.order_id,
                job.sample_id,
                f"{job.shortage}ea",
                f"{job.actual_quantity}ea",
                f"{job.total_time:.1f}분",
            )
            for index, job in enumerate(waiting, start=1)
        ]
        for line in render_table(
            ("순번", "주문번호", "시료", "부족분", "실생산량", "총 생산시간"), rows, QUEUE_COLUMN_WIDTHS
        ):
            print(line)

    def show_live_current_and_queue(
        self,
        snapshot_fn: Callable[
            [], tuple[ProductionJob | None, list[ProductionJob], dict | None]
        ],
    ) -> None:
        for _ in range(LIVE_MAX_REFRESHES):
            current, waiting, detail = snapshot_fn()
            clear_screen()
            print(f"실시간 보기 ({LIVE_REFRESH_SECONDS:.0f}초마다 갱신, Enter 입력 시 종료)")
            self.show_current_and_queue(current, waiting, detail)
            if wait_for_enter_or_timeout(LIVE_REFRESH_SECONDS):
                return

    def show_in_progress(self, current: ProductionJob) -> None:
        bar = render_progress_bar(current.progress)
        print(f"아직 생산 중입니다: 주문 {current.order_id}  {bar}")

    def show_message(self, message: str) -> None:
        print(message)
