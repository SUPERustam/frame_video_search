import logging
import os
from typing import Dict, List

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from quality_plotters.abstract_metric_plotter import AbstractMetricPlotter


class FolderMetricPlotter(AbstractMetricPlotter):
    def __init__(self, input_path: str, output_path: str, hash_names: List[str], search_names: List[str], logger: logging.Logger) -> None:
        super().__init__(input_path, output_path, hash_names, search_names, logger)

    def read_quality_results(self) -> Dict[Dict[List]]:
        quality_results = dict.fromkeys(self.search_names)
        for search_name in self.search_names:
            quality_results[search_name] = dict.fromkeys(self.hash_names)
            for hash_name in self.hash_names:
                quality_results[search_name][hash_name] = pd.read_csv(os.path.join(self.input_path, search_name, hash_name, "quality_metrics.csv"))

        return quality_results

    def plot(self) -> None:
        quality_results = self.read_quality_results()

        folders = next(iter(quality_results.values()))
        folders = next(iter(folders.values()))
        folders = folders["folder"]

        metrics = next(iter(quality_results.values()))
        metrics = next(iter(metrics.values()))
        metrics = metrics.columns[2:]

        for folder in folders:
            self.__plot_folder_metrics(folder, quality_results, metrics)

    def __plot_folder_metrics(self, folder: str, quality_results: Dict[Dict[List]], metrics: pd.Index) -> None:
        fig, axs = plt.subplots(1, len(self.search_names), layout="constrained", figsize=(12, 5 * len(self.search_names)))
        x = np.arange(len(metrics))
        width = 1 / (len(self.hash_names) + 2)
        multiplier = 0

        # Ensure axs is always iterable
        if len(self.search_names) == 1:
            axs = [axs]

        for i, search_name in enumerate(self.search_names):
            for hash_name in self.hash_names:
                offset = width * multiplier
                folder_metrics = quality_results[search_name][hash_name]
                height = np.round(folder_metrics[folder_metrics["folder"] == folder].iloc[:, 2:], 3).values.flatten()

                rects = axs[i].bar(x + offset, height=height, width=width, label=hash_name)
                axs[i].bar_label(rects, padding=3, rotation=55)
                multiplier += 1

            axs[i].set_ylabel("Score")
            axs[i].set_title(f"Folder {folder} metrics on dataset for {search_name}")

            # Center xticks in the middle of each group of bars
            group_center = x + (width * (len(self.hash_names) - 1) / 2)
            axs[i].set_xticks(group_center, metrics)
            axs[i].set_ylim(0, 1.2)

            axs[i].legend(loc="upper left", ncol=len(self.hash_names))
            axs[i].axhline(y=1, color="black", linestyle="--", linewidth=2, label="Perfect")

        plt.savefig(os.path.join(self.output_path, "quality_plots", f"{folder}_metrics.png"))
        plt.close(fig)
