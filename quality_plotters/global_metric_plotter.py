import logging
import os
from typing import List

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from quality_plotters.abstract_metric_plotter import AbstractMetricPlotter


class GlobalMetricPlotter(AbstractMetricPlotter):
    def __init__(self, input_path: str, output_path: str, hash_names: List[str], search_names: List[str], logger: logging.Logger) -> None:
        super().__init__(input_path, output_path, hash_names, search_names, logger)

    def read_quality_results(self) -> pd.DataFrame:
        quality_results = pd.read_csv(os.path.join(self.input_path, "quality_metrics.csv"))
        return quality_results

    def plot(self) -> None:
        quality_results = self.read_quality_results()

        fig, axs = plt.subplots(1, len(self.search_names), layout="constrained", figsize=(12, 5 * len(self.search_names)))
        x = np.arange(len(quality_results.columns) - 2)  # the label locations, -2 because of search_name and hash_name
        width = 1 / (len(self.hash_names) + 2)
        multiplier = 0

        metrics = quality_results.columns[2:]

        # Ensure axs is always iterable
        if len(self.search_names) == 1:
            axs = [axs]

        for i, search_name in enumerate(self.search_names):
            for _, row in quality_results[quality_results["search_name"] == search_name].iterrows():
                offset = width * multiplier
                height = [round(x, 3) for x in row[2:]]

                rects = axs[i].bar(x + offset, height=height, width=width, label=row["hash_name"])
                axs[i].bar_label(rects, padding=3, rotation=55)
                multiplier += 1

            axs[i].set_ylabel("Score")
            axs[i].set_title(f"Global metrics on dataset for {search_name}")

            # Center xticks in the middle of each group of bars
            group_center = x + (width * (len(self.hash_names) - 1) / 2)
            axs[i].set_xticks(group_center, metrics)
            axs[i].set_ylim(0, 1.2)

            axs[i].legend(loc="upper left", ncol=len(self.hash_names))
            axs[i].axhline(y=1, color="black", linestyle="--", linewidth=2, label="Perfect")

        plt.savefig(os.path.join(self.output_path, "quality_plots", "!global_metrics.png"))
