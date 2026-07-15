from app.models.production_job import ProductionJob


class ConsoleProductionView:
    def show_menu(self) -> None:
        print("-" * 40)
        print("[1] 생산 현황 조회  [2] 생산 완료 처리(다음 작업)  [0] 뒤로")

    def get_menu_choice(self) -> str:
        return input("선택 > ").strip()

    def show_current_and_queue(
        self, current: ProductionJob | None, waiting: list[ProductionJob]
    ) -> None:
        if current is None:
            print("생산 중인 작업이 없습니다.")
        else:
            print(
                f"현재 처리 중: 주문 {current.order_id}  부족분 {current.shortage}  "
                f"실생산량 {current.actual_quantity}  총 생산시간 {current.total_time}분"
            )

        if not waiting:
            print("대기 중인 주문이 없습니다.")
            return
        print("대기 중인 주문 (FIFO 순)")
        for index, job in enumerate(waiting, start=1):
            print(
                f"{index}. 주문 {job.order_id}  부족분 {job.shortage}  "
                f"실생산량 {job.actual_quantity}"
            )

    def show_message(self, message: str) -> None:
        print(message)
