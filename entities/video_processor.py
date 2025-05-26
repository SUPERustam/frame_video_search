import logging
import subprocess
import time
from typing import Dict, List, Optional, Tuple

from data_structures.video_hash import VideoHash
from data_structures.video_metadata import VideoMetadata
from data_structures.video_query_metadata import VideoQueryMetadata
from entities.video_keyframe_extractor import VideoKeyframeExtractor
from frame_hashers.abstract_frame_hasher import AbstractFrameHasher


class VideoProcessor:
    def __init__(self, hashers: List[AbstractFrameHasher], logger: logging.Logger, bucket: int, threads: int) -> None:
        self.kfe = VideoKeyframeExtractor(logger=logger)
        self.hashers = hashers
        self.logger = logger
        self.bucket = bucket
        self.threads = threads

    def flv2mp4(self, video_path: str) -> Optional[str]:
        """
        Convert flv to mp4,
        """
        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            f"cash/flv2mp4_{self.bucket}.mp4",
            "-threads",
            str(self.threads),
            "-y",
            "-loglevel",
            "quiet",
        ]

        try:
            subprocess.run(cmd)
        except Exception as e:
            self.logger.error(f"{video_path=} cash/flv2mp4_{self.bucket}.mp4 {e}")
            return None

        return f"cash/flv2mp4_{self.bucket}.mp4"  # for mark that transformation went good

    def cut(self, video_path: str, start_time: str = None, end_time: str = None) -> Optional[str]:
        """
        Cut video from start_time to end_time using ffmpeg.

        Args:
            video_path: Path to the input video file
            start_time: Start time for cutting in format 'hh:mm:ss' or 'ss'
            end_time: End time for cutting in format 'hh:mm:ss' or 'ss'

        Returns:
            Path to the cut video file if successful, None otherwise
        """

        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-ss",
            start_time,
            "-to",
            end_time,
            f'cash_query/cut_{self.bucket}{video_path[video_path.rfind("."):]}',
            "-threads",
            str(self.threads),
            "-y",
            "-loglevel",
            "quiet",
        ]
        subprocess.run(cmd)

        return f'cash_query/cut_{self.bucket}{video_path[video_path.rfind("."):]}'

    def process(self, video_path: str, start_time: str = None, end_time: str = None) -> Optional[Tuple[VideoMetadata, Dict[str, VideoHash]]]:
        original_filepath = video_path

        if start_time and end_time:
            video_path = self.cut(video_path=video_path, start_time=start_time, end_time=end_time)

        start_t = time.perf_counter()
        if video_path[video_path.rfind(".") + 1:] == "flv":
            if not self.flv2mp4(video_path):
                self.logger.error(f"{video_path=} {self.bucket=}")
                return None

            video_path = f"cash/flv2mp4_{self.bucket}.mp4"

        processed = self.kfe.extract(filepath=video_path, original_filepath=original_filepath)
        if not processed:
            return None

        kfe_time = time.perf_counter() - start_t

        metadata, frames = processed

        if start_time and end_time:
            metadata = VideoQueryMetadata(**metadata.__dict__, start_time=start_time, end_time=end_time)

        result_hashes = {hasher.name: hasher.process_frames(frames=frames, filename=metadata.filename, kfe_time=kfe_time) for hasher in self.hashers}

        return metadata, result_hashes
