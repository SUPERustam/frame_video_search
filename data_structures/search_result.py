from dataclasses import dataclass
from typing import List

from data_structures.search_item_result import SearchItemResult


@dataclass
class SearchResult:
    filename_timestamp: str
    results: List[SearchItemResult]
    elapsed_time: float

    def to_json(self) -> dict:
        return {"filename_timestamp": self.filename_timestamp, "results": [result.to_json() for result in self.results]}

    @staticmethod
    def to_csv_header() -> List[str]:
        return ["filename_timestamp", "elapsed_time"]

    def to_csv(self) -> list:
        return [self.filename_timestamp, self.elapsed_time]
