import random

from app.tools.dummy_data_generator import SampleDataGenerator


def test_generate_returns_requested_count():
    generator = SampleDataGenerator(rng=random.Random(42))

    samples = generator.generate(count=5)

    assert len(samples) == 5


def test_generate_produces_unique_ids():
    generator = SampleDataGenerator(rng=random.Random(42))

    samples = generator.generate(count=20)

    assert len({s.sample_id for s in samples}) == 20


def test_generate_produces_always_valid_fields():
    generator = SampleDataGenerator(rng=random.Random(1))

    samples = generator.generate(count=50)

    for sample in samples:
        assert sample.sample_id.strip() != ""
        assert sample.avg_production_time > 0
        assert 0 < sample.yield_rate <= 1
        assert sample.stock >= 0


def test_generate_is_deterministic_for_same_seed():
    first = SampleDataGenerator(rng=random.Random(7)).generate(count=10)
    second = SampleDataGenerator(rng=random.Random(7)).generate(count=10)

    assert [s.to_dict() for s in first] == [s.to_dict() for s in second]


def test_generate_uses_names_from_known_pool():
    generator = SampleDataGenerator(rng=random.Random(3))

    samples = generator.generate(count=10)

    assert all(s.name in SampleDataGenerator.NAME_POOL for s in samples)


def test_generate_avoids_ids_already_in_repository():
    generator = SampleDataGenerator(rng=random.Random(5), existing_ids={"S-001", "S-002"})

    samples = generator.generate(count=3)

    generated_ids = {s.sample_id for s in samples}
    assert generated_ids.isdisjoint({"S-001", "S-002"})
    assert len(generated_ids) == 3
