from cv2.img_hash import BlockMeanHash
from data_structures.frame_hash import FrameHash
from data_structures.video_keyframe import VideoKeyframe
from frame_hashers.abstract_frame_hasher import AbstractFrameHasher


class BlockMeanframeHasher(AbstractFrameHasher):
    def __init__(self, mode: int) -> None:
        super().__init__(name=f"BlockMean{mode}")
        self.hasher = BlockMeanHash.create(mode=mode)
        self.mode = mode
        self.vector_size = 121 if self.mode else 32

    def process(self, frame: VideoKeyframe) -> FrameHash:
        x = self.hasher.compute(frame.frame)
        return FrameHash(vec=x.flatten(), timecode=frame.timecode)
