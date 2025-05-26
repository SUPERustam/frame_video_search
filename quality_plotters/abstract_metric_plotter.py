import abc
import logging
from typing import Dict, List, Optional

import pandas as pd


class AbstractMetricPlotter:
    def __init__(self, input_path: str, output_path: str, hash_names: List[str], search_names: List[str], logger: logging.Logger) -> None:
        self.input_path = input_path
        self.output_path = output_path
        self.hash_names = hash_names
        self.search_names = search_names
        self.logger = logger

    @abc.abstractmethod
    def read_quality_results(self) -> Optional[Dict[str, pd.DataFrame]]:
        pass

    @abc.abstractmethod
    def plot(self) -> None:
        pass
