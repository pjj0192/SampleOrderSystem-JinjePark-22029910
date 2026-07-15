import json
import os
from pathlib import Path

from app.models.sample import Sample


class DuplicateSampleIdError(Exception):
    pass


class SampleNotFoundError(Exception):
    pass


class JsonSampleRepository:
    """JSON-file-backed CRUD repository. Loads existing data from
    ``file_path`` on construction (this is what makes data survive an
    application restart), and write-through persists to disk on every
    mutation via an atomic temp-file-then-replace to avoid partial
    writes corrupting the file."""

    def __init__(self, file_path: str | Path) -> None:
        self._path = Path(file_path)
        self._samples: dict[str, Sample] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        raw_text = self._path.read_text(encoding="utf-8").strip()
        raw_items = json.loads(raw_text) if raw_text else []
        self._samples = {item["sample_id"]: Sample.from_dict(item) for item in raw_items}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        payload = [sample.to_dict() for sample in self._samples.values()]
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp_path, self._path)

    def create(self, sample: Sample) -> None:
        if sample.sample_id in self._samples:
            raise DuplicateSampleIdError(sample.sample_id)
        self._samples[sample.sample_id] = sample
        self._save()

    def get(self, sample_id: str) -> Sample | None:
        return self._samples.get(sample_id)

    def list_all(self) -> list[Sample]:
        return list(self._samples.values())

    def update(self, sample: Sample) -> None:
        if sample.sample_id not in self._samples:
            raise SampleNotFoundError(sample.sample_id)
        self._samples[sample.sample_id] = sample
        self._save()

    def delete(self, sample_id: str) -> None:
        if sample_id not in self._samples:
            raise SampleNotFoundError(sample_id)
        del self._samples[sample_id]
        self._save()
