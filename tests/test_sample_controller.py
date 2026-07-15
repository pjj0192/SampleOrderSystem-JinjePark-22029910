from app.controllers.sample_controller import SampleController
from app.repositories.sample_repository import JsonSampleRepository
from app.services.sample_service import SampleService


class FakeView:
    """Test double standing in for the real console view. Records what the
    controller asks it to show, and replays scripted input instead of
    reading from the real console."""

    def __init__(self, menu_choices=None, register_inputs=None, search_keywords=None):
        self._menu_choices = list(menu_choices or [])
        self._register_inputs = list(register_inputs or [])
        self._search_keywords = list(search_keywords or [])
        self.messages: list[str] = []
        self.shown_samples: list[list] = []
        self.menu_shown_count = 0

    def show_menu(self) -> None:
        self.menu_shown_count += 1

    def get_menu_choice(self) -> str:
        return self._menu_choices.pop(0)

    def get_register_input(self) -> dict:
        return self._register_inputs.pop(0)

    def get_search_keyword(self) -> str:
        return self._search_keywords.pop(0)

    def show_samples(self, samples) -> None:
        self.shown_samples.append(list(samples))

    def show_message(self, message: str) -> None:
        self.messages.append(message)


def make_controller(tmp_path, **view_kwargs):
    service = SampleService(JsonSampleRepository(tmp_path / "samples.json"))
    view = FakeView(**view_kwargs)
    return SampleController(service, view), service, view


def test_handle_register_success_shows_confirmation(tmp_path):
    controller, service, view = make_controller(
        tmp_path,
        register_inputs=[
            {
                "sample_id": "S-001",
                "name": "실리콘 웨이퍼-8인치",
                "avg_production_time": 0.5,
                "yield_rate": 0.92,
            }
        ],
    )

    controller.handle_register()

    assert service.list_all()[0].sample_id == "S-001"
    assert any("S-001" in m for m in view.messages)


def test_handle_register_invalid_input_shows_error_not_raises(tmp_path):
    controller, service, view = make_controller(
        tmp_path,
        register_inputs=[
            {"sample_id": "S-001", "name": "x", "avg_production_time": 0, "yield_rate": 0.9}
        ],
    )

    controller.handle_register()

    assert service.list_all() == []
    assert len(view.messages) == 1


def test_handle_list_shows_all_registered_samples(tmp_path):
    controller, service, view = make_controller(tmp_path)
    service.register("S-001", "x", 1.0, 0.9)

    controller.handle_list()

    assert [s.sample_id for s in view.shown_samples[0]] == ["S-001"]


def test_handle_search_shows_matching_samples(tmp_path):
    controller, service, view = make_controller(tmp_path, search_keywords=["silicon"])
    service.register("S-001", "Silicon Wafer", 1.0, 0.9)
    service.register("S-002", "GaN Epitaxial", 1.0, 0.9)

    controller.handle_search()

    assert [s.sample_id for s in view.shown_samples[0]] == ["S-001"]


def test_run_shows_sample_list_by_default_on_entry(tmp_path):
    controller, service, view = make_controller(tmp_path, menu_choices=["0"])
    service.register("S-001", "x", 1.0, 0.9)

    controller.run()

    assert [s.sample_id for s in view.shown_samples[0]] == ["S-001"]


def test_run_dispatches_menu_choices_until_exit(tmp_path):
    controller, service, view = make_controller(tmp_path, menu_choices=["2", "0"])

    controller.run()

    assert view.menu_shown_count == 2
    assert len(view.shown_samples) == 2


def test_run_shows_error_message_for_unknown_choice(tmp_path):
    controller, service, view = make_controller(tmp_path, menu_choices=["9", "0"])

    controller.run()

    assert any("잘못된" in m for m in view.messages)
