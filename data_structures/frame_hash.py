from dataclasses import dataclass

import numpy as np


@dataclass
class FrameHash:
    vec: np.ndarray
    timecode: float

    def to_json(self) -> dict:
        return {"vec": self.vec.tolist(), "timecode": self.timecode}
