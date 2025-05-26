from dataclasses import dataclass
from typing import List


@dataclass
class VideoMetadata:
    filename: str
    fps: float
    duration: float
    width: int
    height: int
    frames_count: int

    def to_csv(self) -> list:
        return [self.filename, self.fps, self.duration, self.width, self.height, self.frames_count]

    @staticmethod
    def to_csv_header() -> List[str]:
        return ["filename", "fps", "duration", "width", "height", "frames_count"]
