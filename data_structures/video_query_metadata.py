from dataclasses import dataclass
from typing import List

from data_structures.video_metadata import VideoMetadata


@dataclass
class VideoQueryMetadata(VideoMetadata):
    start_time: str
    end_time: str

    def to_csv(self) -> list:
        return [self.filename, self.start_time, self.end_time, self.fps, self.duration, self.width, self.height, self.frames_count]

    @staticmethod
    def to_csv_header() -> List[str]:
        return ["filename", "start_time", "end_time", "fps", "duration", "width", "height", "frames_count"]
