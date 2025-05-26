import abc
import time
from typing import List

from data_structures.frame_hash import FrameHash
from data_structures.video_hash import VideoHash
from data_structures.video_keyframe import VideoKeyframe


class AbstractFrameHasher:
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.vector_size: int = -1

    @abc.abstractmethod
    def process(self, frame: VideoKeyframe) -> FrameHash:
        pass

    def process_frames(self, frames: List[VideoKeyframe], filename: str, kfe_time: float) -> VideoHash:
        start_timer = time.perf_counter()
        frames = [self.process(frame) for frame in frames]
        end_timer = time.perf_counter()

        return VideoHash(filename=filename, frames=frames, elapsed_time=end_timer - start_timer, full_elapsed_time=kfe_time + end_timer - start_timer)
