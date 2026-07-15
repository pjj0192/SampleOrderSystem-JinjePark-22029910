from app.models.sample import Sample
from app.repositories.sample_repository import JsonSampleRepository


class SampleService:
    def __init__(self, repository: JsonSampleRepository) -> None:
        self._repository = repository

    def register(
        self,
        sample_id: str,
        name: str,
        avg_production_time: float,
        yield_rate: float,
    ) -> Sample:
        sample = Sample(
            sample_id=sample_id,
            name=name,
            avg_production_time=avg_production_time,
            yield_rate=yield_rate,
        )
        self._repository.create(sample)
        return sample

    def list_all(self) -> list[Sample]:
        return self._repository.list_all()

    def get(self, sample_id: str) -> Sample | None:
        return self._repository.get(sample_id)

    def search_by_name(self, keyword: str) -> list[Sample]:
        needle = keyword.strip().lower()
        return [s for s in self._repository.list_all() if needle in s.name.lower()]
