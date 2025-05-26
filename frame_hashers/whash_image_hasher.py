import cv2
import imagehash
from PIL import Image
from data_structures.frame_hash import FrameHash
from data_structures.video_keyframe import VideoKeyframe
from frame_hashers.abstract_frame_hasher import AbstractFrameHasher


class WHashImageHasher(AbstractFrameHasher):
    def __init__(self) -> None:
        super().__init__(name="whash")
        self.hasher = imagehash.whash
        self.vector_size = 64

    def process(self, frame: VideoKeyframe) -> FrameHash:
        x = cv2.cvtColor(frame.frame, cv2.COLOR_BGR2RGB)  # turn frame from BGR to RGB
        x = self.hasher(Image.fromarray(x))
        x = x.hash  # turn from string representation (ImageHash algo) to np.ndarray
        return FrameHash(vec=x.flatten(), timecode=frame.timecode)  # make 1D instead of 2D np.ndarray
