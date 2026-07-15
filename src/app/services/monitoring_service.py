from app.models.order import OrderStatus

ORDER_SUMMARY_STATUSES = (
    OrderStatus.RESERVED,
    OrderStatus.CONFIRMED,
    OrderStatus.PRODUCING,
    OrderStatus.RELEASED,
)

PENDING_DEMAND_STATUSES = (OrderStatus.RESERVED, OrderStatus.PRODUCING)

SUFFICIENT_RATIO_THRESHOLD = 0.5

STATUS_SUFFICIENT = "여유"
STATUS_SHORT = "부족"
STATUS_DEPLETED = "고갈"


class MonitoringService:
    """Aggregates read-only data from SampleRepository/OrderRepository.
    No aggregation logic lives in the repositories themselves."""

    def __init__(self, sample_repository, order_repository) -> None:
        self._sample_repository = sample_repository
        self._order_repository = order_repository

    def order_status_summary(self) -> dict[str, int]:
        orders = self._order_repository.list_all()
        counts = {status.value: 0 for status in ORDER_SUMMARY_STATUSES}
        for order in orders:
            if order.status.value in counts:
                counts[order.status.value] += 1
        return counts

    def stock_summary(self) -> list[dict]:
        samples = self._sample_repository.list_all()
        return [self._stock_entry(sample) for sample in samples]

    def _stock_entry(self, sample) -> dict:
        pending_demand = sum(
            order.quantity
            for order in self._order_repository.list_by_sample(sample.sample_id)
            if order.status in PENDING_DEMAND_STATUSES
        )
        ratio = sample.stock / max(pending_demand, 1)
        return {
            "sample_id": sample.sample_id,
            "name": sample.name,
            "stock": sample.stock,
            "ratio": ratio,
            "status": self._classify(sample.stock, ratio),
        }

    @staticmethod
    def _classify(stock: int, ratio: float) -> str:
        if stock == 0:
            return STATUS_DEPLETED
        if ratio >= SUFFICIENT_RATIO_THRESHOLD:
            return STATUS_SUFFICIENT
        return STATUS_SHORT
