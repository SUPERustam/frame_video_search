from dataclasses import dataclass
from typing import List

from data_structures.quality_result_folder import QualityResultFolder


@dataclass
class QualityResult:
    search_name: str
    hash_name: str
    results_per_folder: List[QualityResultFolder]

    @staticmethod
    def to_csv_header() -> List[str]:
        return ["search_name", "hash_name", "MRR", "mAP", "Recall", "Found original"]

    def to_csv(self) -> list:
        num_videos = sum(result.num_videos for result in self.results_per_folder)

        mrr = sum(result.mrr * result.num_videos for result in self.results_per_folder) / num_videos
        mp = sum(result.mp * result.num_videos for result in self.results_per_folder) / num_videos
        recall = sum(result.recall * result.num_videos for result in self.results_per_folder) / num_videos
        found_original = sum(result.found_original * result.num_videos for result in self.results_per_folder) / num_videos

        return [self.search_name, self.hash_name, mrr, mp, recall, found_original]
