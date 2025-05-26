from cv2.img_hash import MarrHildrethHash
from data_structures.frame_hash import FrameHash
from data_structures.video_keyframe import VideoKeyframe
from frame_hashers.abstract_frame_hasher import AbstractFrameHasher


class MarrHildrethframeHasher(AbstractFrameHasher):
    def __init__(self) -> None:
        super().__init__(name="Marr-Hildreth")
        self.hasher = MarrHildrethHash.create()
        self.vector_size = 72

    def process(self, frame: VideoKeyframe) -> FrameHash:
        x = self.hasher.compute(frame.frame)
        return FrameHash(vec=x.flatten(), timecode=frame.timecode)
