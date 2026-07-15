from app.models.production_job import ProductionJob
from app.views.progress_bar import render_progress_bar


class ConsoleProductionView:
    def show_menu(self) -> None:
        print("-" * 60)
        print("[1] 생산 현황 조회  [2] 생산 완료 처리(다음 작업)  [0] 뒤로")

    def get_menu_choice(self) -> str:
        return input("선택 > ").strip()

    def show_current_and_queue(
        self, current: ProductionJob | None, waiting: list[ProductionJob]
    ) -> None:
        print("-" * 60)
        print("현재 처리 중")
        if current is None:
            print("  생산 중인 작업이 없습니다.")
        else:
            bar = render_progress_bar(current.progress)
            print(f"  주문 {current.order_id}  ({current.sample_id})")
            print(
                f"  부족분 {current.shortage}ea  실생산량 {current.actual_quantity}ea  "
                f"총 생산시간 {current.total_time:.1f}분"
            )
            print(f"  진행률 {bar}")

        print()
        print(f"대기 중인 주문 (FIFO 순, {len(waiting)}건)")
        if not waiting:
            print("  대기 중인 주문이 없습니다.")
            return
        for index, job in enumerate(waiting, start=1):
            print(
                f"  {index}. 주문 {job.order_id}  ({job.sample_id})  "
                f"부족분 {job.shortage}ea  실생산량 {job.actual_quantity}ea  "
                f"총 생산시간 {job.total_time:.1f}분"
            )

    def show_in_progress(self, current: ProductionJob) -> None:
        bar = render_progress_bar(current.progress)
        print(f"아직 생산 중입니다: 주문 {current.order_id}  {bar}")

    def show_message(self, message: str) -> None:
        print(message)
