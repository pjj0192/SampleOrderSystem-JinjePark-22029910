from app.controllers.monitoring_controller import MonitoringController


class FakeService:
    def __init__(self):
        self.order_status_summary_called = False
        self.stock_summary_called = False

    def order_status_summary(self):
        self.order_status_summary_called = True
        return {"RESERVED": 1}

    def stock_summary(self):
        self.stock_summary_called = True
        return [{"sample_id": "S-001"}]


class FakeView:
    def __init__(self, choices):
        self._choices = iter(choices)
        self.shown_order_summary = None
        self.shown_stock_summary = None
        self.messages = []

    def show_menu(self) -> None:
        pass

    def get_menu_choice(self) -> str:
        return next(self._choices)

    def show_order_status_summary(self, summary) -> None:
        self.shown_order_summary = summary

    def show_stock_summary(self, entries) -> None:
        self.shown_stock_summary = entries

    def show_message(self, message: str) -> None:
        self.messages.append(message)


def test_choice_1_shows_order_status_summary():
    service = FakeService()
    view = FakeView(["1", "0"])
    controller = MonitoringController(service, view)

    controller.run()

    assert service.order_status_summary_called
    assert view.shown_order_summary == {"RESERVED": 1}


def test_choice_2_shows_stock_summary():
    service = FakeService()
    view = FakeView(["2", "0"])
    controller = MonitoringController(service, view)

    controller.run()

    assert service.stock_summary_called
    assert view.shown_stock_summary == [{"sample_id": "S-001"}]


def test_choice_0_exits_without_calling_service():
    service = FakeService()
    view = FakeView(["0"])
    controller = MonitoringController(service, view)

    controller.run()

    assert not service.order_status_summary_called
    assert not service.stock_summary_called


def test_invalid_choice_shows_message_and_continues():
    service = FakeService()
    view = FakeView(["9", "0"])
    controller = MonitoringController(service, view)

    controller.run()

    assert view.messages == ["잘못된 선택입니다."]
