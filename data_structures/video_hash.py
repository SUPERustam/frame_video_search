from dataclasses import dataclass
from typing import List

from data_structures.frame_hash import FrameHash


@dataclass
class VideoHash:
    filename: str
    frames: List[FrameHash]
    elapsed_time: float
    full_elapsed_time: float

    def to_json(self) -> dict:
        return {"filename": self.filename, "frames": [frame.to_json() for frame in self.frames]}

    @staticmethod
    def to_csv_header() -> List[str]:
        return ["filename", "elapsed_time_per_hash", "full_elapsed_time"]

    def to_csv(self) -> list:
        return [self.filename, self.elapsed_time, self.full_elapsed_time]
