from dataclasses import dataclass
from typing import List


@dataclass
class QualityResultFolder:
    folder: str
    num_videos: int
    mrr: float
    mp: float  # mAP
    recall: float
    found_original: float

    @staticmethod
    def to_csv_header() -> List[str]:
        return ["folder", "Number of videos", "MRR", "mAP", "Recall", "Found original"]

    def to_csv(self) -> list:
        return [self.folder, self.num_videos, self.mrr, self.mp, self.recall, self.found_original]
