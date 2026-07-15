import random

from app.models.sample import Sample
from app.repositories.sample_repository import JsonSampleRepository

MIN_AVG_PRODUCTION_TIME = 0.1
MAX_AVG_PRODUCTION_TIME = 2.0
MIN_YIELD_RATE = 0.7
MAX_YIELD_RATE = 1.0
MIN_INITIAL_STOCK = 0
MAX_INITIAL_STOCK = 500


class SampleDataGenerator:
    """Generates syntactically-and-semantically valid dummy Sample data.
    Takes a random.Random instance rather than using the global random
    module, so tests can seed it for deterministic, reproducible output."""

    NAME_POOL = (
        "실리콘 웨이퍼-8인치",
        "GaN 에피택셜-4인치",
        "SiC 파워기판-6인치",
        "포토레지스트-PR7",
        "산화막 웨이퍼-SiO2",
    )

    def __init__(self, rng: random.Random, existing_ids: set[str] | None = None) -> None:
        self._rng = rng
        self._existing_ids = set(existing_ids or set())

    def generate(self, count: int) -> list[Sample]:
        samples = []
        for _ in range(count):
            sample_id = self._next_sample_id()
            self._existing_ids.add(sample_id)
            samples.append(
                Sample(
                    sample_id=sample_id,
                    name=self._rng.choice(self.NAME_POOL),
                    avg_production_time=round(
                        self._rng.uniform(MIN_AVG_PRODUCTION_TIME, MAX_AVG_PRODUCTION_TIME), 2
                    ),
                    yield_rate=round(self._rng.uniform(MIN_YIELD_RATE, MAX_YIELD_RATE), 2),
                    stock=self._rng.randint(MIN_INITIAL_STOCK, MAX_INITIAL_STOCK),
                )
            )
        return samples

    def _next_sample_id(self) -> str:
        next_number = len(self._existing_ids) + 1
        candidate = f"S-{next_number:03d}"
        while candidate in self._existing_ids:
            next_number += 1
            candidate = f"S-{next_number:03d}"
        return candidate


def generate_and_store(
    repository: JsonSampleRepository, count: int, rng: random.Random
) -> list[Sample]:
    """Generates count dummy samples and persists each one into repository
    via create(), so the data is actually added to the connected store
    rather than merely printed."""
    existing_ids = {s.sample_id for s in repository.list_all()}
    generator = SampleDataGenerator(rng=rng, existing_ids=existing_ids)
    samples = generator.generate(count)
    for sample in samples:
        repository.create(sample)
    return samples
