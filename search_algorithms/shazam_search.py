import logging
from collections import defaultdict
from typing import Any, Dict, List

import numpy as np
from data_structures.annoy_db import AnnoyDB
from data_structures.distance_item_result import DistanceItemResult
from data_structures.search_item_result import SearchItemResult


class ShazamSearch:
    def __init__(
        self,
        annoy_db: AnnoyDB,
        logger: logging.Logger,
        bucket: int,
        threads: int,
    ) -> None:
        self.logger = logger
        self.bucket = bucket
        self.threads = threads
        self.annoy_db = annoy_db

    def search_frame(self, frame: Dict[str, Any], k: int = 10) -> List[DistanceItemResult]:
        """
        Search a frame and return a list of distance item results.
        """
        results = self.annoy_db.annoy_index.get_nns_by_vector(frame["vec"], k, search_k=-1, include_distances=True)

        results = tuple(zip(results[0], results[1]))

        ans = []
        for result in results:
            frame_metadata = self.annoy_db.db_index[result[0]]
            ans.append(
                DistanceItemResult(
                    filename=frame_metadata[0],
                    timestamp_delta=frame_metadata[2],
                    distance=result[1],
                )
            )

        return ans

    def process_frames(self, frames: List[Dict[str, Any]], topk: int = 10) -> List[SearchItemResult]:
        """
        Process a list of frames and return a list of search item results.

        Example of frames:
        ```
        [
            {
                "vec": [1, 5, 0, 3, ...],
                "timecode": "5.45"
            },
            ...
        ]
        ```
        """

        frames_result = [self.search_frame(frame, k=10) for frame in frames]

        filename4hst = defaultdict(list)

        for frame, frame_result in zip(frames, frames_result):
            for item in frame_result:
                if item.timestamp_delta - frame["timecode"] >= -1.5:  # skip frames which can't be found in the video
                    rev_dist = 1 if item.distance == 0 else 1 / item.distance

                    filename4hst[item.filename].append([item.timestamp_delta - frame["timecode"], rev_dist])

        for k, v in filename4hst.items():
            filename4hst[k] = list(zip(*v))

        results = []

        for k, v in filename4hst.items():
            bin_min = np.floor(min(v[0]))
            bin_max = np.ceil(max(v[0]))
            bins = np.arange(bin_min, bin_max + 1, 1)

            hst, hst_delta = np.histogram(v[0], bins=bins, weights=v[1])

            if len(hst) == 0:
                item = SearchItemResult(filename=k, timestamp_delta=float(v[0][0]), weight=float(v[1][0]))
            else:
                top_idx = np.argmax(hst)
                top_coef = hst[top_idx]
                item = SearchItemResult(filename=k, timestamp_delta=float(hst_delta[top_idx]), weight=float(top_coef))

            results.append(item)

        results = sorted(results, key=lambda x: x.weight, reverse=True)

        return results[: min(topk, len(results))]
