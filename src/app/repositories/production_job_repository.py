import json
import os
from pathlib import Path

from app.models.production_job import ProductionJob


class ProductionJobNotFoundError(Exception):
    pass


class JsonProductionJobRepository:
    """JSON-file-backed CRUD repository for ProductionJob, mirroring
    JsonSampleRepository/JsonOrderRepository. Without this, the FIFO
    production queue only lived in ProductionService's in-memory deque --
    an app restart would lose every queued job while the order it belonged
    to stayed stuck at PRODUCING forever, since nothing was left to
    complete it."""

    def __init__(self, file_path: str | Path) -> None:
        self._path = Path(file_path)
        self._jobs: dict[str, ProductionJob] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        raw_text = self._path.read_text(encoding="utf-8").strip()
        raw_items = json.loads(raw_text) if raw_text else []
        self._jobs = {item["job_id"]: ProductionJob.from_dict(item) for item in raw_items}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        payload = [job.to_dict() for job in self._jobs.values()]
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp_path, self._path)

    def create(self, job: ProductionJob) -> None:
        self._jobs[job.job_id] = job
        self._save()

    def list_all(self) -> list[ProductionJob]:
        return list(self._jobs.values())

    def update(self, job: ProductionJob) -> None:
        if job.job_id not in self._jobs:
            raise ProductionJobNotFoundError(job.job_id)
        self._jobs[job.job_id] = job
        self._save()

    def delete(self, job_id: str) -> None:
        if job_id not in self._jobs:
            raise ProductionJobNotFoundError(job_id)
        del self._jobs[job_id]
        self._save()
