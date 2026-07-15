from dataclasses import asdict, dataclass


@dataclass
class Sample:
    sample_id: str
    name: str
    avg_production_time: float
    yield_rate: float
    stock: int = 0

    def __post_init__(self) -> None:
        if not self.sample_id or not self.sample_id.strip():
            raise ValueError("sample_id must not be blank")
        if self.avg_production_time <= 0:
            raise ValueError("avg_production_time must be positive")
        if not (0 < self.yield_rate <= 1):
            raise ValueError("yield_rate must be within (0, 1]")
        if self.stock < 0:
            raise ValueError("stock must be >= 0")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Sample":
        return cls(**data)
