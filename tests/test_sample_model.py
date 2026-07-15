import pytest

from app.models.sample import Sample


def test_creates_sample_with_valid_fields():
    sample = Sample(
        sample_id="S-001",
        name="실리콘 웨이퍼-8인치",
        avg_production_time=0.5,
        yield_rate=0.92,
    )

    assert sample.sample_id == "S-001"
    assert sample.stock == 0


def test_rejects_blank_sample_id():
    with pytest.raises(ValueError):
        Sample(sample_id="  ", name="x", avg_production_time=1.0, yield_rate=0.9)


def test_rejects_non_positive_avg_production_time():
    with pytest.raises(ValueError):
        Sample(sample_id="S-001", name="x", avg_production_time=0, yield_rate=0.9)


@pytest.mark.parametrize("yield_rate", [0, -0.1, 1.1])
def test_rejects_yield_rate_out_of_range(yield_rate):
    with pytest.raises(ValueError):
        Sample(sample_id="S-001", name="x", avg_production_time=1.0, yield_rate=yield_rate)


def test_rejects_negative_stock():
    with pytest.raises(ValueError):
        Sample(sample_id="S-001", name="x", avg_production_time=1.0, yield_rate=0.9, stock=-1)


def test_to_dict_and_from_dict_round_trip():
    original = Sample(
        sample_id="S-001",
        name="실리콘 웨이퍼-8인치",
        avg_production_time=0.5,
        yield_rate=0.92,
        stock=480,
    )

    restored = Sample.from_dict(original.to_dict())

    assert restored == original
