import logging
import os
from typing import List, Optional, Tuple

import cv2
from data_structures.video_keyframe import VideoKeyframe
from data_structures.video_metadata import VideoMetadata


class VideoKeyframeExtractor:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

    def extract(self, filepath: str, original_filepath: str, interval: float = 0.5) -> Optional[Tuple[VideoMetadata, List[VideoKeyframe]]]:
        """Choose one frame every 0.5 seconds
        Used logging with logger instance to catch almost all exceptions
        """

        # Check file is eligible for opencv open
        if not os.path.isfile(filepath):
            self.logger.error(f"Video file does not exist: {original_filepath}")
            return None

        video = cv2.VideoCapture(filepath)

        if not video.isOpened():
            self.logger.error(f"Cannot open video file {original_filepath}")
            return None

        try:
            fps = video.get(cv2.CAP_PROP_FPS)
            frames_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

            metadata = VideoMetadata(
                filename=original_filepath,
                fps=fps,
                duration=frames_count / fps,
                width=int(video.get(cv2.CAP_PROP_FRAME_WIDTH)),
                height=int(video.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                frames_count=frames_count,
            )
        except Exception as e:
            self.logger.error(f"Exception {e} on file {original_filepath}")
            return None

        frame_interval = int(fps * interval)
        frames = self.__process_frames(video, metadata.frames_count, frame_interval, fps, original_filepath)
        if frames is None:
            return None

        video.release()
        return metadata, frames

    def __process_frames(self, video: cv2.VideoCapture, frames_count: int, frame_interval: int, fps: float, original_filepath: str) -> List[VideoKeyframe]:
        frames = []
        for frame_count in range(frames_count):
            try:
                ret, frame = video.read()
            except Exception as e:
                self.logger.error(f"Exception {e} on file {original_filepath}")
                return None

            if frame_count % frame_interval != 0:
                continue

            timestamp = frame_count / fps
            frames.append(VideoKeyframe(frame=frame, timecode=round(2 * timestamp, 2) / 2))

        return frames
