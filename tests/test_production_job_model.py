from datetime import datetime

import pytest

from app.models.production_job import ProductionJob

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
    }
    fields.update(overrides)
    return ProductionJob(**fields)


def test_creates_job_with_valid_fields():
    job = make_job()

    assert job.job_id == "JOB-0001"
    assert job.shortage == 16
    assert job.actual_quantity == 20
    assert job.progress == 0.0


def test_rejects_blank_job_id():
    with pytest.raises(ValueError):
        make_job(job_id="  ")


def test_rejects_non_positive_shortage():
    with pytest.raises(ValueError):
        make_job(shortage=0)


def test_rejects_non_positive_actual_quantity():
    with pytest.raises(ValueError):
        make_job(actual_quantity=0)


def test_rejects_actual_quantity_less_than_shortage():
    with pytest.raises(ValueError):
        make_job(shortage=20, actual_quantity=16)


def test_rejects_non_positive_total_time():
    with pytest.raises(ValueError):
        make_job(total_time=0)


@pytest.mark.parametrize("progress", [-0.1, 1.1])
def test_rejects_progress_out_of_range(progress):
    with pytest.raises(ValueError):
        make_job(progress=progress)


def test_accepts_progress_boundaries():
    assert make_job(progress=0.0).progress == 0.0
    assert make_job(progress=1.0).progress == 1.0
