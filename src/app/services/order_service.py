from collections.abc import Callable
from datetime import datetime

from app.models.order import Order, OrderStatus
from app.repositories.order_repository import JsonOrderRepository
from app.repositories.sample_repository import JsonSampleRepository, SampleNotFoundError
from app.services.production_service import ProductionService


class InvalidOrderStateError(Exception):
    pass


class OrderService:
    """Owns all order status transitions (PRD.md §5) -- Controllers/Views
    never mutate Order.status directly."""

    def __init__(
        self,
        order_repository: JsonOrderRepository,
        sample_repository: JsonSampleRepository,
        production_service: ProductionService,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._order_repository = order_repository
        self._sample_repository = sample_repository
        self._production_service = production_service
        self._clock = clock

    def reserve(self, sample_id: str, customer_name: str, quantity: int) -> Order:
        sample = self._sample_repository.get(sample_id)
        if sample is None:
            raise SampleNotFoundError(sample_id)

        now = self._clock()
        order = Order(
            order_id=self._generate_order_id(now),
            sample_id=sample_id,
            customer_name=customer_name,
            quantity=quantity,
            status=OrderStatus.RESERVED,
            created_at=now,
            updated_at=now,
        )
        self._order_repository.create(order)
        return order

    def _generate_order_id(self, now: datetime) -> str:
        date_part = now.strftime("%Y%m%d")
        sequence = len(self._order_repository.list_all()) + 1
        return f"ORD-{date_part}-{sequence:04d}"

    def approve(self, order_id: str) -> Order:
        order = self._order_repository.get(order_id)
        if order.status != OrderStatus.RESERVED:
            raise InvalidOrderStateError(
                f"order {order_id} is {order.status.value}, not RESERVED"
            )
        sample = self._sample_repository.get(order.sample_id)

        if sample.stock >= order.quantity:
            sample.stock -= order.quantity
            self._sample_repository.update(sample)
            order.status = OrderStatus.CONFIRMED
            order.updated_at = self._clock()
            self._order_repository.update(order)
        else:
            self._production_service.enqueue(order, sample)
            order.status = OrderStatus.PRODUCING
            order.updated_at = self._clock()
            self._order_repository.update(order)

        return order

    def reject(self, order_id: str) -> Order:
        order = self._order_repository.get(order_id)
        if order.status != OrderStatus.RESERVED:
            raise InvalidOrderStateError(
                f"order {order_id} is {order.status.value}, not RESERVED"
            )
        order.status = OrderStatus.REJECTED
        order.updated_at = self._clock()
        self._order_repository.update(order)
        return order

    def complete_production(self) -> Order | None:
        """PRD.md §7.5: the completed job's actual_quantity is received into
        stock in full (yield_rate only sized how much to produce -- it does
        not mean part of the output is scrapped), then the order's quantity
        is deducted to confirm it. Whatever remains
        (actual_quantity - shortage) stays in stock as surplus."""
        job = self._production_service.advance()
        if job is None:
            return None

        order = self._order_repository.get(job.order_id)
        sample = self._sample_repository.get(job.sample_id)

        sample.stock += job.actual_quantity
        sample.stock -= order.quantity
        self._sample_repository.update(sample)

        order.status = OrderStatus.CONFIRMED
        order.updated_at = self._clock()
        self._order_repository.update(order)

        return order

    def get_order(self, order_id: str) -> Order | None:
        return self._order_repository.get(order_id)

    def resync_production_queue(self) -> None:
        """Startup repair: re-enqueues any order left at PRODUCING with no
        matching ProductionJob in the queue -- e.g. because the production
        queue file didn't exist yet the last time that transition happened.
        Without this, such an order is stuck at PRODUCING forever, since
        nothing is left to actually drive it to completion (this is the
        'monitoring shows PRODUCING but nothing is producing' symptom)."""
        queued_order_ids = {job.order_id for job in self._production_service.queue()}
        producing_orders = sorted(
            (o for o in self._order_repository.list_all() if o.status == OrderStatus.PRODUCING),
            key=lambda o: o.updated_at,
        )
        for order in producing_orders:
            if order.order_id in queued_order_ids:
                continue
            sample = self._sample_repository.get(order.sample_id)
            self._production_service.enqueue(order, sample)

    def list_reserved(self) -> list[Order]:
        return [
            order
            for order in self._order_repository.list_all()
            if order.status == OrderStatus.RESERVED
        ]

    def total_order_count(self) -> int:
        return len(self._order_repository.list_all())

    def list_confirmed(self) -> list[Order]:
        return [
            order
            for order in self._order_repository.list_all()
            if order.status == OrderStatus.CONFIRMED
        ]

    def ship(self, order_id: str) -> Order:
        order = self._order_repository.get(order_id)
        if order.status != OrderStatus.CONFIRMED:
            raise InvalidOrderStateError(
                f"order {order_id} is {order.status.value}, not CONFIRMED"
            )
        order.status = OrderStatus.RELEASED
        order.updated_at = self._clock()
        self._order_repository.update(order)
        return order
