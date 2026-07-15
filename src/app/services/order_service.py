from collections.abc import Callable
from datetime import datetime

from app.models.order import Order, OrderStatus
from app.repositories.order_repository import JsonOrderRepository
from app.repositories.sample_repository import JsonSampleRepository, SampleNotFoundError


class OrderService:
    """Owns all order status transitions (PRD.md §5) -- Controllers/Views
    never mutate Order.status directly."""

    def __init__(
        self,
        order_repository: JsonOrderRepository,
        sample_repository: JsonSampleRepository,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._order_repository = order_repository
        self._sample_repository = sample_repository
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
