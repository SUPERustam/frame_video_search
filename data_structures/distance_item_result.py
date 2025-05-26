from dataclasses import dataclass
from typing import Optional


@dataclass
class DistanceItemResult:
    filename: str
    timestamp_delta: Optional[float]
    distance: float

    def to_json(self) -> dict:
        return {"filename": self.filename, "timestamp_delta": self.timestamp_delta, "distance": self.distance}
