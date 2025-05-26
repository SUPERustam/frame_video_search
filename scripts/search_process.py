import argparse
import csv
import glob
import json
import logging
import math
import os
import sys
import time
from typing import Dict, List

from data_structures.search_result import SearchResult
from entities.annoy_processor import AnnoyProcessor
from frame_hashers.block_mean_image_hasher import BlockMeanframeHasher
from frame_hashers.dhash_image_hasher import DHashImageHasher
from frame_hashers.marr_hildreth_image_hasher import MarrHildrethframeHasher
from frame_hashers.phash_image_hasher import PHashImageHasher
from frame_hashers.radial_variance_image_hasher import RadialVarianceframeHasher
from frame_hashers.whash_image_hasher import WHashImageHasher
from search_algorithms.shazam_search import ShazamSearch


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


def save_search_results(name2search: Dict[str, SearchResult], bucket: int) -> None:
    for search_name, search_result in name2search.items():
        with open(search_name, "w", encoding="utf-8") as f:
            json.dump(search_result.to_json(), f)

        csv_filepath = os.path.join(search_name[: search_name.rfind("/")], f"time_{bucket}.csv")

        if not os.path.exists(csv_filepath) or os.path.getsize(csv_filepath) == 0:
            with open(csv_filepath, "w", encoding="utf-8") as f:
                csv_writer = csv.writer(f, delimiter=",")
                csv_writer.writerow(SearchResult.to_csv_header())
                csv_writer.writerow(search_result.to_csv())
                continue

        with open(csv_filepath, "a", encoding="utf-8") as f:
            csv_writer = csv.writer(f, delimiter=",")
            csv_writer.writerow(search_result.to_csv())


def check_corectly_number_across_hash_function(hash_names: List, queries: Dict, output_path: str, logger: logging.Logger) -> None:
    len_query_paths = -1
    for hash_name in hash_names:
        queries[hash_name] = glob.glob(os.path.join(output_path, "query_hashes", hash_name, "*.json"))
        if len_query_paths > len(queries[hash_name]):
            logger.error("The number of query videos is not the same for all hash functions")
            sys.exit()
        else:
            len_query_paths = len(queries[hash_name])


def main() -> None:
    description = "\n".join([
        "Search all query videos in db. Try:",
        "PYTHONPATH=. python scripts/search_process.py -i core_dataset -o core_dataset",
    ])

    hashers = {
        "Marr-Hildreth": MarrHildrethframeHasher(),
        "BlockMean0": BlockMeanframeHasher(mode=0),
        "BlockMean1": BlockMeanframeHasher(mode=1),
        "RadialVariance": RadialVarianceframeHasher(),
        "phash": PHashImageHasher(),
        "whash": WHashImageHasher(),
        "dhash": DHashImageHasher(),
    }
    searchers = {
        "Shazam": ShazamSearch,
    }
    hash_names = list(hashers.keys())
    search_names = list(searchers.keys())

    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--hash", help="hash function to use", choices=hash_names + ["all"], default="all")
    parser.add_argument("--search", help="search algorithm to use", choices=search_names + ["all"], default="all")
    parser.add_argument("-i", "--input", help="input directory of video", type=str, required=True)
    parser.add_argument("-o", "--output", help="output directory to store results", type=str, required=True)
    parser.add_argument("-B", "--buckets", help="number of buckets (default: %(default)d)", type=int, default=1)
    parser.add_argument("-b", "--bucket", help="index of bucket (0...buckets-1, default: %(default)d)", type=int, default=0)
    args = parser.parse_args()

    input_path = args.input
    output_path = args.output

    logger = get_logger(f"{output_path}/search_process_{args.bucket}.log", args.bucket, args.buckets)

    if not os.path.exists(input_path):
        logger.error(f"--input={input_path} doesn't exist")
        return

    os.makedirs(output_path, exist_ok=True)

    if 0 > args.bucket or args.bucket >= args.buckets:
        logger.error(f"The --bucket={args.bucket} must be 0 < --bucket < --buckets={args.buckets}")
        return

    hash_names = hash_names if args.hash == "all" else [args.hash]
    search_names = search_names if args.search == "all" else [args.search]

    search_engines = {}

    # setup db, prepare search algorithms
    for hash_name in hash_names:
        annoy_processor = AnnoyProcessor(
            hasher=hashers[hash_name],
            logger=logger,
            bucket=args.bucket,
            threads=max(1, int(os.cpu_count() / args.buckets)),
        )

        for search_name in search_names:
            os.makedirs(os.path.join(output_path, search_name, hash_name), exist_ok=True)

            search_engines.setdefault(search_name, {})[hash_name] = searchers[search_name](
                annoy_db=annoy_processor.load_annoy_db_from_disk(os.path.join(output_path, "hashes", hash_name)),
                logger=logger,
                bucket=args.bucket,
                threads=max(1, int(os.cpu_count() / args.buckets)),
            )

        logger.info(f'Annoy index successfully loaded: {os.path.join(output_path, "hashes", hash_name)}')

    # prepare query videos
    queries = {}
    queries[hash_names[0]] = glob.glob(os.path.join(output_path, "query_hashes", hash_names[0], "*.json"))
    len_query_paths = len(queries[hash_names[0]])
    check_corectly_number_across_hash_function(hash_names=hash_names, queries=queries, output_path=output_path, logger=logger)

    start_with_video = math.ceil(len_query_paths * args.bucket / args.buckets)
    end_with_video = min(len_query_paths, math.ceil(len_query_paths * (args.bucket + 1) / args.buckets))

    # search
    for index_video in range(start_with_video, end_with_video):
        for hash_name in hash_names:
            name2search = {}

            query = queries[hash_name][index_video]
            query_name = os.path.basename(query)

            logger.info(f"i={index_video} {hash_name=} {query=}")

            with open(query, "r") as f:
                data = json.load(f)
                frames = data["frames"]

            for search_name in search_names:
                start_timer = time.perf_counter()
                search_result = search_engines[search_name][hash_name].process_frames(frames)

                elapsed_time = time.perf_counter() - start_timer

                name2search[os.path.join(output_path, search_name, hash_name, query_name)] = SearchResult(
                    filename_timestamp=query_name[:-5],
                    results=search_result,
                    elapsed_time=elapsed_time,
                )

            save_search_results(name2search=name2search, bucket=args.bucket)

    logger.info(f"Done threads={max(1, int(os.cpu_count() / args.buckets))}")


if __name__ == "__main__":
    main()
