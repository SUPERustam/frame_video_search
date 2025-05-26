from dataclasses import dataclass
from typing import Optional


@dataclass
class SearchItemResult:
    filename: str
    timestamp_delta: Optional[float]
    weight: float

    def to_json(self) -> dict:
        return {"filename": self.filename, "timestamp_delta": self.timestamp_delta, "weight": self.weight}
