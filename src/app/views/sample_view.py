from app.models.sample import Sample


class ConsoleSampleView:
    """Console I/O only, no business logic (see CLAUDE.md layering rules)."""

    def show_menu(self) -> None:
        print("-" * 40)
        print("[1] 시료 등록  [2] 시료 목록  [3] 시료 검색  [0] 뒤로")

    def get_menu_choice(self) -> str:
        return input("선택 > ").strip()

    def get_register_input(self) -> dict:
        sample_id = input("시료 ID > ").strip()
        name = input("이름 > ").strip()
        avg_production_time = float(input("평균 생산시간(min/ea) > ").strip())
        yield_rate = float(input("수율(0~1) > ").strip())
        return {
            "sample_id": sample_id,
            "name": name,
            "avg_production_time": avg_production_time,
            "yield_rate": yield_rate,
        }

    def get_search_keyword(self) -> str:
        return input("검색어 > ").strip()

    def show_samples(self, samples: list[Sample]) -> None:
        if not samples:
            print("등록된 시료가 없습니다.")
            return
        print(f"{'ID':<10}{'이름':<20}{'생산시간':<12}{'수율':<8}{'재고':<8}")
        for sample in samples:
            print(
                f"{sample.sample_id:<10}{sample.name:<20}"
                f"{sample.avg_production_time:<12}{sample.yield_rate:<8}{sample.stock:<8}"
            )

    def show_message(self, message: str) -> None:
        print(message)
