import json
import os
from pathlib import Path

from app.models.order import Order


class DuplicateOrderIdError(Exception):
    pass


class OrderNotFoundError(Exception):
    pass


class JsonOrderRepository:
    """JSON-file-backed CRUD repository for Order, mirroring
    JsonSampleRepository: loads existing data on construction (restart
    durability) and write-through persists via temp-file + os.replace
    (atomic write)."""

    def __init__(self, file_path: str | Path) -> None:
        self._path = Path(file_path)
        self._orders: dict[str, Order] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        raw_text = self._path.read_text(encoding="utf-8").strip()
        raw_items = json.loads(raw_text) if raw_text else []
        self._orders = {item["order_id"]: Order.from_dict(item) for item in raw_items}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        payload = [order.to_dict() for order in self._orders.values()]
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp_path, self._path)

    def create(self, order: Order) -> None:
        if order.order_id in self._orders:
            raise DuplicateOrderIdError(order.order_id)
        self._orders[order.order_id] = order
        self._save()

    def get(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)

    def list_all(self) -> list[Order]:
        return list(self._orders.values())

    def list_by_sample(self, sample_id: str) -> list[Order]:
        return [order for order in self._orders.values() if order.sample_id == sample_id]

    def update(self, order: Order) -> None:
        if order.order_id not in self._orders:
            raise OrderNotFoundError(order.order_id)
        self._orders[order.order_id] = order
        self._save()
