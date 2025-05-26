import logging
import os
from typing import List

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from quality_plotters.abstract_metric_plotter import AbstractMetricPlotter


class TimeMetricPlotter(AbstractMetricPlotter):
    def __init__(self, input_path: str, output_path: str, hash_names: List[str], search_names: List[str], logger: logging.Logger) -> None:
        super().__init__(input_path, output_path, hash_names, search_names, logger)

    def read_quality_results(self) -> dict:
        quality_results = dict.fromkeys(self.search_names)
        for search_name in self.search_names:
            quality_results[search_name] = dict.fromkeys(["mean_search_time", "mean_hash_time", "mean_kfe_time"])
            for metric in quality_results[search_name].keys():
                quality_results[search_name][metric] = dict.fromkeys(self.hash_names)

        video_metadata = pd.read_csv(os.path.join(self.input_path, "metadata.csv"))
        mean_video_duration = video_metadata["duration"].mean()

        for search_name in self.search_names:
            for hash_name in self.hash_names:
                search_time = pd.read_csv(os.path.join(self.input_path, search_name, hash_name, "time.csv"))
                hash_time = pd.read_csv(os.path.join(self.input_path, "hashes", hash_name, "time.csv"))

                mean_search_time = search_time["elapsed_time"].mean()
                mean_hash_time = hash_time["elapsed_time_per_hash"].mean()
                mean_kfe_time = hash_time["full_elapsed_time"].mean() - mean_hash_time

                quality_results[search_name]["mean_search_time"][hash_name] = mean_search_time * 3600 / mean_video_duration
                quality_results[search_name]["mean_hash_time"][hash_name] = mean_hash_time * 3600 / mean_video_duration
                quality_results[search_name]["mean_kfe_time"][hash_name] = mean_kfe_time * 3600 / mean_video_duration

        return quality_results

    def plot(self) -> None:
        quality_results = self.read_quality_results()

        fig, axs = plt.subplots(1, len(self.search_names), layout="constrained", figsize=(10, 5 * len(self.search_names)))

        width = 0.7
        bottom = np.zeros(len(self.hash_names), dtype=np.float64)

        # Ensure axs is always iterable
        if len(self.search_names) == 1:
            axs = [axs]

        for i, search_name in enumerate(self.search_names):
            mean_kfe_time = tuple(quality_results[search_name]["mean_kfe_time"].values())[0]
            del quality_results[search_name]["mean_kfe_time"]  # because kfe time is same for all hash functions

            for metric, mean in quality_results[search_name].items():
                p = axs[i].bar(self.hash_names, mean.values(), width, label=metric, bottom=bottom)
                bottom += np.array(tuple(mean.values()))
                axs[i].bar_label(p, label_type="center")

            axs[i].set_ylabel("Score")
            axs[i].set_title(f"Time metrics on dataset for {search_name} in seconds/1 hour video (KFE time: {mean_kfe_time: .2f})")
            axs[i].legend(loc="upper left", ncol=len(self.hash_names))

        plt.savefig(os.path.join(self.output_path, "quality_plots", "!time_metrics.png"))
