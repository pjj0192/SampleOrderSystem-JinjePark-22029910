import random

from app.models.sample import Sample
from app.repositories.sample_repository import JsonSampleRepository
from app.tools.dummy_data_generator import generate_and_store


def test_generate_and_store_persists_requested_count(tmp_path):
    repo = JsonSampleRepository(tmp_path / "samples.json")

    created = generate_and_store(repo, count=10, rng=random.Random(1))

    assert len(created) == 10
    assert {s.sample_id for s in repo.list_all()} == {s.sample_id for s in created}


def test_generate_and_store_avoids_colliding_with_existing_data(tmp_path):
    file_path = tmp_path / "samples.json"
    repo = JsonSampleRepository(file_path)
    repo.create(Sample("S-001", "기존 시료", 1.0, 0.9))

    generate_and_store(repo, count=5, rng=random.Random(2))

    all_ids = [s.sample_id for s in repo.list_all()]
    assert len(all_ids) == len(set(all_ids)) == 6


def test_generate_and_store_survives_repository_restart(tmp_path):
    file_path = tmp_path / "samples.json"
    repo = JsonSampleRepository(file_path)

    generate_and_store(repo, count=7, rng=random.Random(3))

    restarted_repo = JsonSampleRepository(file_path)
    assert len(restarted_repo.list_all()) == 7
