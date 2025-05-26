import argparse
import csv
import json
import logging
import math
import os
from typing import Dict

from data_structures.video_hash import VideoHash
from data_structures.video_query_metadata import VideoQueryMetadata
from entities.video_annotation_parser import VideoAnnotationParser
from entities.video_processor import VideoProcessor
from frame_hashers.block_mean_image_hasher import BlockMeanframeHasher
from frame_hashers.dhash_image_hasher import DHashImageHasher
from frame_hashers.marr_hildreth_image_hasher import MarrHildrethframeHasher
from frame_hashers.phash_image_hasher import PHashImageHasher
from frame_hashers.radial_variance_image_hasher import RadialVarianceframeHasher
from frame_hashers.whash_image_hasher import WHashImageHasher


def get_logger(log_path: str, bucket: int, buckets: int) -> logging.Logger:
    logger = logging.getLogger(__name__)
    bucket += 1

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] [bucket=%(bucket)s/%(buckets)s] - %(message)s",
        handlers=[
            logging.FileHandler(log_path, mode="w"),
            logging.StreamHandler(),
        ],
    )

    logging.getLogger("matplotlib").setLevel(logging.WARNING)

    # Add bucket and buckets as extra attributes to the logger
    logger = logging.LoggerAdapter(logger, {"bucket": bucket, "buckets": buckets})
    return logger


def save_hashes(name2hash: Dict[str, VideoHash], hashes_dir: str, video_name: str, bucket: int) -> None:
    for hash_name, video_hash in name2hash.items():
        with open(
                os.path.join(hashes_dir, hash_name, f"{video_name}.json"),
                "w",
                encoding="utf-8",
        ) as f:
            json.dump(video_hash.to_json(), f)

        csv_filepath = os.path.join(hashes_dir, hash_name, f"time_{bucket}.csv")
        if not os.path.exists(csv_filepath) or os.path.getsize(csv_filepath) == 0:
            with open(csv_filepath, "w", encoding="utf-8") as f:
                csv_writer = csv.writer(f, delimiter=",")
                csv_writer.writerow(VideoHash.to_csv_header())
                csv_writer.writerow(video_hash.to_csv())
                continue

        with open(csv_filepath, "a", encoding="utf-8") as f:
            csv_writer = csv.writer(f, delimiter=",")
            csv_writer.writerow(video_hash.to_csv())


def main() -> None:
    description = "\n".join([
        "Upload all query videos to db. Hashing included.",
        "Try: PYTHONPATH=. python scripts/query_process.py -i /home/superustam/jam/light_video_copy_detection/data/annotation/ -o core_dataset",
    ])

    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-i", "--input", help="input directory of video annotations", type=str, required=True)
    parser.add_argument("-o", "--output", help="output directory to store processed dataset", type=str, required=True)
    parser.add_argument("-B", "--buckets", help="number of buckets (default: %(default)d)", type=int, default=1)
    parser.add_argument("-b", "--bucket", help="index of bucket (0...buckets-1, default: %(default)d)", type=int, default=0)
    args = parser.parse_args()

    # Example
    # output_path = "core_dataset"
    # videos_dir = "/home/superustam/jam/light_video_copy_detection/data/annotation/"

    query_annotation = args.input
    output_path = args.output

    hashers = [
        MarrHildrethframeHasher(),
        BlockMeanframeHasher(mode=0),
        BlockMeanframeHasher(mode=1),
        RadialVarianceframeHasher(),
        PHashImageHasher(),
        WHashImageHasher(),
        DHashImageHasher(),
    ]

    os.makedirs(output_path, exist_ok=True)
    os.makedirs("cash_query", exist_ok=True)
    os.makedirs("cash", exist_ok=True)

    logger = get_logger(f"{output_path}/query_process_{args.bucket}.log", args.bucket, args.buckets)

    if not os.path.exists(query_annotation):
        logger.error(f"--input={query_annotation} doesn't exist")
        return

    if 0 > args.bucket or args.bucket >= args.buckets:
        logger.error(f"The --bucket={args.bucket} must be 0 < --bucket < --buckets={args.buckets}")
        return

    hashes_dir = os.path.join(output_path, "query_hashes")
    for hasher in hashers:
        os.makedirs(os.path.join(hashes_dir, hasher.name), exist_ok=True)

    video_processor = VideoProcessor(
        hashers=hashers,
        logger=logger,
        bucket=args.bucket,
        threads=max(1, int(os.cpu_count() / args.buckets)),
    )
    video_annotation_parser = VideoAnnotationParser(logger=logger)

    query_paths = video_annotation_parser.parse(annotation_path=query_annotation)

    len_query_paths = len(query_paths)

    start_with_video = math.ceil(len_query_paths * args.bucket / args.buckets)
    end_with_video = min(len_query_paths, math.ceil(len_query_paths * (args.bucket + 1) / args.buckets))

    with open(os.path.join(output_path, f"query_metadata_{args.bucket}.csv"), "w", newline="") as f:
        csv_writer = csv.writer(f, delimiter=",")
        csv_writer.writerow(VideoQueryMetadata.to_csv_header())

        for i, query_path in enumerate(query_paths[start_with_video:end_with_video]):
            logger.info(f"{args.bucket=} i={start_with_video + i} {query_path[0]=} {query_path[1:]}")

            result = video_processor.process(
                video_path=query_path[0],
                start_time=query_path[1],
                end_time=query_path[2],
            )

            if not result:
                logger.error(f"{args.bucket=} {query_path[0]=} {query_path[1:]}")
                continue

            metadata, name2hash = result

            save_hashes(
                name2hash=name2hash,
                hashes_dir=hashes_dir,
                video_name=os.path.basename(f'{query_path[0]}_{query_path[1].replace(".", "-")}_{query_path[2].replace(".", "-")}'),
                bucket=args.bucket,
            )

            csv_writer.writerow(metadata.to_csv())

    logger.info(f"Done {args.bucket=} threads={max(1, int(os.cpu_count() / args.buckets))}")


if __name__ == "__main__":
    main()
