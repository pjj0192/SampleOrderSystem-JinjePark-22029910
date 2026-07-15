import pytest

from app.repositories.sample_repository import DuplicateSampleIdError, JsonSampleRepository
from app.services.sample_service import SampleService


def make_service(tmp_path):
    return SampleService(JsonSampleRepository(tmp_path / "samples.json"))


def test_register_creates_and_stores_sample(tmp_path):
    service = make_service(tmp_path)

    sample = service.register(
        sample_id="S-001",
        name="실리콘 웨이퍼-8인치",
        avg_production_time=0.5,
        yield_rate=0.92,
    )

    assert sample.sample_id == "S-001"
    assert service.list_all() == [sample]


def test_register_duplicate_id_raises(tmp_path):
    service = make_service(tmp_path)
    service.register("S-001", "x", 1.0, 0.9)

    with pytest.raises(DuplicateSampleIdError):
        service.register("S-001", "y", 1.0, 0.9)


def test_register_invalid_fields_propagates_value_error(tmp_path):
    service = make_service(tmp_path)

    with pytest.raises(ValueError):
        service.register("S-001", "x", avg_production_time=0, yield_rate=0.9)


def test_search_by_name_matches_case_insensitive_substring(tmp_path):
    service = make_service(tmp_path)
    service.register("S-001", "Silicon Wafer", 1.0, 0.9)
    service.register("S-002", "GaN Epitaxial", 1.0, 0.9)

    result = service.search_by_name("silicon")

    assert [s.sample_id for s in result] == ["S-001"]


def test_search_by_name_no_match_returns_empty_list(tmp_path):
    service = make_service(tmp_path)
    service.register("S-001", "Silicon Wafer", 1.0, 0.9)

    assert service.search_by_name("nonexistent") == []
