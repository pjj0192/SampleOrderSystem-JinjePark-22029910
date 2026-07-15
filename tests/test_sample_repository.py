import json

import pytest

from app.models.sample import Sample
from app.repositories.sample_repository import (
    DuplicateSampleIdError,
    JsonSampleRepository,
    SampleNotFoundError,
)


def make_sample(sample_id="S-001", **overrides):
    fields = {
        "sample_id": sample_id,
        "name": "실리콘 웨이퍼-8인치",
        "avg_production_time": 0.5,
        "yield_rate": 0.92,
    }
    fields.update(overrides)
    return Sample(**fields)


def test_create_persists_to_file_and_is_readable(tmp_path):
    file_path = tmp_path / "samples.json"
    repo = JsonSampleRepository(file_path)

    repo.create(make_sample())

    assert repo.get("S-001").name == "실리콘 웨이퍼-8인치"
    raw = json.loads(file_path.read_text(encoding="utf-8"))
    assert raw == [make_sample().to_dict()]


def test_list_all_returns_every_created_sample(tmp_path):
    repo = JsonSampleRepository(tmp_path / "samples.json")
    repo.create(make_sample("S-001"))
    repo.create(make_sample("S-002"))

    assert {s.sample_id for s in repo.list_all()} == {"S-001", "S-002"}


def test_get_missing_sample_returns_none(tmp_path):
    repo = JsonSampleRepository(tmp_path / "samples.json")
    assert repo.get("S-999") is None


def test_create_duplicate_id_raises(tmp_path):
    repo = JsonSampleRepository(tmp_path / "samples.json")
    repo.create(make_sample("S-001"))

    with pytest.raises(DuplicateSampleIdError):
        repo.create(make_sample("S-001"))


def test_update_modifies_existing_sample_and_persists(tmp_path):
    file_path = tmp_path / "samples.json"
    repo = JsonSampleRepository(file_path)
    repo.create(make_sample("S-001", stock=0))

    repo.update(make_sample("S-001", stock=100))

    assert repo.get("S-001").stock == 100
    raw = json.loads(file_path.read_text(encoding="utf-8"))
    assert raw[0]["stock"] == 100


def test_update_missing_sample_raises(tmp_path):
    repo = JsonSampleRepository(tmp_path / "samples.json")

    with pytest.raises(SampleNotFoundError):
        repo.update(make_sample("S-999"))


def test_delete_removes_sample_and_persists(tmp_path):
    file_path = tmp_path / "samples.json"
    repo = JsonSampleRepository(file_path)
    repo.create(make_sample("S-001"))

    repo.delete("S-001")

    assert repo.get("S-001") is None
    raw = json.loads(file_path.read_text(encoding="utf-8"))
    assert raw == []


def test_delete_missing_sample_raises(tmp_path):
    repo = JsonSampleRepository(tmp_path / "samples.json")

    with pytest.raises(SampleNotFoundError):
        repo.delete("S-999")


def test_no_leftover_tmp_file_after_write(tmp_path):
    file_path = tmp_path / "samples.json"
    repo = JsonSampleRepository(file_path)

    repo.create(make_sample("S-001"))

    leftover_tmp_files = list(tmp_path.glob("*.tmp"))
    assert leftover_tmp_files == []
