from datetime import datetime

import pytest

from app.models.production_job import ProductionJob
from app.repositories.production_job_repository import (
    JsonProductionJobRepository,
    ProductionJobNotFoundError,
)

NOW = datetime(2026, 4, 16, 9, 0, 0)


def make_job(**overrides):
    fields = {
        "job_id": "JOB-0001",
        "order_id": "ORD-0001",
        "sample_id": "S-001",
        "shortage": 16,
        "actual_quantity": 20,
        "total_time": 10.0,
        "enqueued_at": NOW,
        "started_at": NOW,
    }
    fields.update(overrides)
    return ProductionJob(**fields)


def test_create_then_list_all_returns_the_job(tmp_path):
    repo = JsonProductionJobRepository(tmp_path / "queue.json")

    repo.create(make_job())

    assert [job.job_id for job in repo.list_all()] == ["JOB-0001"]


def test_data_persists_across_repository_restart(tmp_path):
    path = tmp_path / "queue.json"
    JsonProductionJobRepository(path).create(make_job(started_at=None))

    reloaded = JsonProductionJobRepository(path)

    [job] = reloaded.list_all()
    assert job.job_id == "JOB-0001"
    assert job.started_at is None
    assert job.enqueued_at == NOW


def test_update_persists_started_at_change(tmp_path):
    path = tmp_path / "queue.json"
    repo = JsonProductionJobRepository(path)
    repo.create(make_job(started_at=None))

    job = repo.list_all()[0]
    job.started_at = NOW
    repo.update(job)

    reloaded = JsonProductionJobRepository(path)
    assert reloaded.list_all()[0].started_at == NOW


def test_delete_removes_the_job(tmp_path):
    path = tmp_path / "queue.json"
    repo = JsonProductionJobRepository(path)
    repo.create(make_job())

    repo.delete("JOB-0001")

    assert repo.list_all() == []
    assert JsonProductionJobRepository(path).list_all() == []


def test_update_unknown_job_raises(tmp_path):
    repo = JsonProductionJobRepository(tmp_path / "queue.json")

    with pytest.raises(ProductionJobNotFoundError):
        repo.update(make_job())


def test_delete_unknown_job_raises(tmp_path):
    repo = JsonProductionJobRepository(tmp_path / "queue.json")

    with pytest.raises(ProductionJobNotFoundError):
        repo.delete("JOB-9999")
