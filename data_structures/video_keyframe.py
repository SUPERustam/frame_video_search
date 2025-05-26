from dataclasses import dataclass

import numpy as np


@dataclass
class VideoKeyframe:
    frame: np.ndarray
    timecode: float
