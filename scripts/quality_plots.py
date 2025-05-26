import argparse
import csv
import json
import logging
import os
from typing import Dict

from data_structures.search_result import SearchResult
from frame_hashers.block_mean_image_hasher import BlockMeanframeHasher
from frame_hashers.dhash_image_hasher import DHashImageHasher
from frame_hashers.marr_hildreth_image_hasher import MarrHildrethframeHasher
from frame_hashers.phash_image_hasher import PHashImageHasher
from frame_hashers.radial_variance_image_hasher import RadialVarianceframeHasher
from frame_hashers.whash_image_hasher import WHashImageHasher
from quality_plotters.folder_metric_plotter import FolderMetricPlotter
from quality_plotters.global_metric_plotter import GlobalMetricPlotter
from quality_plotters.time_metric_plotter import TimeMetricPlotter
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


def main() -> None:
    description = "\n".join([
        "Run quality tests on db. Try:",
        "PYTHONPATH=. python scripts/quality_plots.py -i core_dataset -o core_dataset",
        "",
        "NOTICE: bucket/buckets ignored because quality tests are fast enough",
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
    parser.add_argument("-i", "--input", help="input directory of results", type=str, required=True)
    parser.add_argument("-o", "--output", help="output directory to store quality plots", type=str, required=True)
    parser.add_argument("-B", "--buckets", help="number of buckets (default: %(default)d)", type=int, default=1)
    parser.add_argument("-b", "--bucket", help="index of bucket (0...buckets-1, default: %(default)d)", type=int, default=0)
    args = parser.parse_args()

    input_path = args.input
    output_path = args.output

    logger = get_logger(f"{output_path}/quality_plots_{args.bucket}.log", args.bucket, args.buckets)

    if not os.path.exists(input_path):
        logger.error(f"--input={input_path} doesn't exist")
        return

    os.makedirs(output_path, exist_ok=True)
    os.makedirs(os.path.join(output_path, "quality_plots"), exist_ok=True)

    if 0 > args.bucket or args.bucket >= args.buckets:
        logger.error(f"The --bucket={args.bucket} must be 0 < --bucket < --buckets={args.buckets}")
        return

    hash_names = hash_names if args.hash == "all" else [args.hash]
    search_names = search_names if args.search == "all" else [args.search]

    # plotting
    metric_plotters = [
        GlobalMetricPlotter(input_path, output_path, hash_names, search_names, logger),
        FolderMetricPlotter(input_path, output_path, hash_names, search_names, logger),
        TimeMetricPlotter(input_path, output_path, hash_names, search_names, logger)
    ]

    for metric_plotter in metric_plotters:
        metric_plotter.plot()

    logger.info("Done")


if __name__ == "__main__":
    main()
