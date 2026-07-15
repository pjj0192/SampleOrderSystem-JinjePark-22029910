from typing import Protocol

from app.models.sample import Sample
from app.repositories.sample_repository import DuplicateSampleIdError
from app.services.sample_service import SampleService


class SampleView(Protocol):
    """Interface the controller depends on. The real console view and the
    tests' FakeView both satisfy this shape, so the controller never
    references a concrete console implementation."""

    def show_menu(self) -> None: ...
    def get_menu_choice(self) -> str: ...
    def get_register_input(self) -> dict | None: ...
    def get_search_keyword(self) -> str: ...
    def show_samples(self, samples: list[Sample]) -> None: ...
    def show_message(self, message: str) -> None: ...


class SampleController:
    def __init__(self, service: SampleService, view: SampleView) -> None:
        self._service = service
        self._view = view

    def handle_register(self) -> None:
        data = self._view.get_register_input()
        if data is None:
            self._view.show_message("시료 등록을 취소했습니다.")
            return
        try:
            sample = self._service.register(**data)
        except (ValueError, DuplicateSampleIdError) as error:
            self._view.show_message(f"등록 실패: {error}")
            return
        self._view.show_message(f"등록 완료: {sample.sample_id}")

    def handle_list(self) -> None:
        self._view.show_samples(self._service.list_all())

    def handle_search(self) -> None:
        keyword = self._view.get_search_keyword()
        self._view.show_samples(self._service.search_by_name(keyword))

    def run(self) -> None:
        actions = {
            "1": self.handle_register,
            "2": self.handle_list,
            "3": self.handle_search,
        }
        self.handle_list()
        while True:
            self._view.show_menu()
            choice = self._view.get_menu_choice()
            if choice == "0":
                return
            action = actions.get(choice)
            if action is None:
                self._view.show_message("잘못된 선택입니다.")
                continue
            action()
