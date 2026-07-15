import math

from app.models.sample import Sample
from app.views.console_format import render_table, section_title
from app.views.input_helpers import (
    InputCancelled,
    prompt_float_or_cancel,
    prompt_nonblank_str_or_cancel,
)

COLUMN_WIDTHS = (10, 20, 10, 8, 8)
PAGE_SIZE = 8


class ConsoleSampleView:
    """Console I/O only, no business logic (see CLAUDE.md layering rules)."""

    def show_menu(self) -> None:
        print()
        for line in section_title("시료 관리"):
            print(line)
        print("  [1] 시료 등록   [2] 시료 목록   [3] 시료 검색   [0] 뒤로")

    def get_menu_choice(self) -> str:
        return input("선택 > ").strip()

    def get_register_input(self) -> dict | None:
        """Returns None if the user types 0 at any prompt to cancel out of
        a registration they entered by mistake, instead of a filled-in
        dict."""
        try:
            sample_id = prompt_nonblank_str_or_cancel("시료 ID (0=취소) > ")
            name = prompt_nonblank_str_or_cancel("이름 (0=취소) > ")
            avg_production_time = prompt_float_or_cancel(
                "평균 생산시간(min/ea) (0=취소) > ", min_value=0, exclusive_min=True
            )
            yield_rate = prompt_float_or_cancel(
                "수율(0~1) (0=취소) > ", min_value=0, max_value=1, exclusive_min=True
            )
        except InputCancelled:
            return None
        return {
            "sample_id": sample_id,
            "name": name,
            "avg_production_time": avg_production_time,
            "yield_rate": yield_rate,
        }

    def get_search_keyword(self) -> str:
        return input("검색어 > ").strip()

    def show_samples(self, samples: list[Sample]) -> None:
        print()
        if not samples:
            print("등록된 시료가 없습니다.")
            return
        total_pages = math.ceil(len(samples) / PAGE_SIZE)
        page = 0
        while True:
            start = page * PAGE_SIZE
            self._show_samples_page(samples[start : start + PAGE_SIZE])
            print(f"페이지 {page + 1}/{total_pages}  (총 {len(samples)}건)")
            if total_pages <= 1:
                return
            choice = input("[N] 다음 페이지  그 외 입력 시 종료 > ").strip().upper()
            if choice != "N":
                return
            page = (page + 1) % total_pages

    def _show_samples_page(self, samples: list[Sample]) -> None:
        rows = [
            (
                sample.sample_id,
                sample.name,
                f"{sample.avg_production_time}분",
                sample.yield_rate,
                f"{sample.stock}ea",
            )
            for sample in samples
        ]
        for line in render_table(("ID", "이름", "생산시간", "수율", "재고"), rows, COLUMN_WIDTHS):
            print(line)

    def show_message(self, message: str) -> None:
        print(message)
