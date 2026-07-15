import sys

from app.controllers.main_menu_controller import MainMenuController
from app.controllers.monitoring_controller import MonitoringController
from app.controllers.order_approval_controller import OrderApprovalController
from app.controllers.order_reservation_controller import OrderReservationController
from app.controllers.production_controller import ProductionController
from app.controllers.sample_controller import SampleController
from app.controllers.shipment_controller import ShipmentController
from app.repositories.order_repository import JsonOrderRepository
from app.repositories.production_job_repository import JsonProductionJobRepository
from app.repositories.sample_repository import JsonSampleRepository
from app.services.monitoring_service import MonitoringService
from app.services.order_service import OrderService
from app.services.production_service import ProductionService
from app.services.sample_service import SampleService
from app.views.main_menu_view import ConsoleMainMenuView
from app.views.monitoring_view import ConsoleMonitoringView
from app.views.order_approval_view import ConsoleOrderApprovalView
from app.views.order_reservation_view import ConsoleOrderReservationView
from app.views.production_view import ConsoleProductionView
from app.views.sample_view import ConsoleSampleView
from app.views.shipment_view import ConsoleShipmentView

SAMPLES_FILE = "data/samples.json"
ORDERS_FILE = "data/orders.json"
PRODUCTION_QUEUE_FILE = "data/production_queue.json"


def _force_utf8_console() -> None:
    """Windows terminals often default to a legacy codepage (e.g. cp949),
    which mangles the Korean text this app prints. reconfigure() raises
    on streams that don't support it (e.g. some redirected/piped setups),
    so guard defensively."""
    for stream in (sys.stdout, sys.stdin):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def build_main_menu_controller() -> MainMenuController:
    sample_repository = JsonSampleRepository(SAMPLES_FILE)
    order_repository = JsonOrderRepository(ORDERS_FILE)
    production_job_repository = JsonProductionJobRepository(PRODUCTION_QUEUE_FILE)

    production_service = ProductionService(repository=production_job_repository)
    sample_service = SampleService(sample_repository)
    order_service = OrderService(order_repository, sample_repository, production_service)
    order_service.resync_production_queue()
    monitoring_service = MonitoringService(sample_repository, order_repository)

    sample_controller = SampleController(sample_service, ConsoleSampleView())
    order_reservation_controller = OrderReservationController(
        order_service, sample_service, ConsoleOrderReservationView()
    )
    order_approval_controller = OrderApprovalController(
        order_service, sample_service, production_service, ConsoleOrderApprovalView()
    )
    monitoring_controller = MonitoringController(monitoring_service, ConsoleMonitoringView())
    production_controller = ProductionController(
        order_service, production_service, sample_service, ConsoleProductionView()
    )
    shipment_controller = ShipmentController(order_service, ConsoleShipmentView())

    return MainMenuController(
        sample_service=sample_service,
        order_service=order_service,
        production_service=production_service,
        sample_controller=sample_controller,
        order_reservation_controller=order_reservation_controller,
        order_approval_controller=order_approval_controller,
        monitoring_controller=monitoring_controller,
        production_controller=production_controller,
        shipment_controller=shipment_controller,
        view=ConsoleMainMenuView(),
    )


def main() -> None:
    _force_utf8_console()
    build_main_menu_controller().run()


if __name__ == "__main__":
    main()
