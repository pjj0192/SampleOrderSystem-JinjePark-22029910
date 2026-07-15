from app.views.console_format import centered, divider, title_block


class ConsoleMainMenuView:
    def show_summary_and_menu(self, summary: dict) -> None:
        print()
        for line in title_block("반도체 시료 생산주문관리 시스템"):
            print(line)
        print()
        print(centered(f"시스템 시간  {summary['current_time']}"))
        print(
            centered(
                f"등록 시료 {summary['sample_count']}종   총 재고 {summary['total_stock']}ea   "
                f"전체 주문 {summary['total_orders']}건   생산라인 대기 "
                f"{summary['production_queue_length']}건"
            )
        )
        print()
        pending_tasks = [task for task in summary["pending_tasks"] if task["count"] > 0]
        if pending_tasks:
            pending_text = "   ".join(f"{t['label']} {t['count']}건" for t in pending_tasks)
            print(centered(f"[대기 중인 작업] {pending_text}"))
        else:
            print(centered("대기 중인 작업이 없습니다."))
        print()
        print(divider("-"))
        print("  [1] 시료 관리          [2] 시료 주문")
        print("  [3] 주문 승인/거절      [4] 모니터링")
        print("  [5] 생산라인 조회       [6] 출고 처리")
        print("  [0] 종료")
        print(divider("-"))

    def get_menu_choice(self) -> str:
        return input("선택 > ").strip()

    def show_message(self, message: str) -> None:
        print(message)
