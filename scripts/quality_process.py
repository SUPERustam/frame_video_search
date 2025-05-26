import argparse
import csv
import glob
import json
import logging
import os
from typing import Dict, List, Tuple, Type, Union

from data_structures.quality_result import QualityResult
from data_structures.quality_result_folder import QualityResultFolder
from frame_hashers.block_mean_image_hasher import BlockMeanframeHasher
from frame_hashers.dhash_image_hasher import DHashImageHasher
from frame_hashers.marr_hildreth_image_hasher import MarrHildrethframeHasher
from frame_hashers.phash_image_hasher import PHashImageHasher
from frame_hashers.radial_variance_image_hasher import RadialVarianceframeHasher
from frame_hashers.whash_image_hasher import WHashImageHasher
from search_algorithms.shazam_search import ShazamSearch


def process_query_results(
    data: Dict,
    ground_truth_data: Dict[Tuple[str, str, str], List[Tuple[str, str, str]]],
    query2folder: Dict[Tuple[str, str, str], str],
    metrics_per_folder: Dict[str, QualityResultFolder],
) -> Dict[str, QualityResultFolder]:
    query_key = tuple(data["filename_timestamp"].split("_"))
    query_folder = query2folder[query_key]
    metrics_per_folder[query_folder].num_videos += 1

    ground_truth_results = [query[0] for query in ground_truth_data[query_key]]
    results = data["results"]

    found_ground_truth = 0  # for MRR and mAP
    ap = 0.0  # for mAP
    tp = 0  # for recall

    for rank, item in enumerate(results, 1):
        item_name = os.path.basename(item["filename"])

        if item_name in ground_truth_results or item_name == query_key[0]:
            # Found original
            if item_name.strip() == query_key[0].strip():
                metrics_per_folder[query_folder].found_original += 1

            # MRR
            if found_ground_truth == 0:
                metrics_per_folder[query_folder].mrr += 1 / rank

            # Recall
            tp += 1

            # mAP
            found_ground_truth += 1
            ap += found_ground_truth / rank

    if found_ground_truth != 0:
        metrics_per_folder[query_folder].mp += ap / found_ground_truth

    metrics_per_folder[query_folder].recall += tp / (len(ground_truth_results) + 1)

    return metrics_per_folder


def calculate_metrics(
    experiments_dir: str,
    ground_truth_data: Dict[Tuple[str, str, str], List[Tuple[str, str, str]]],
    query2folder: Dict[Tuple[str, str, str], str],
    logger: logging.Logger,
) -> Dict[str, QualityResultFolder]:
    # TODO: calculate also metrics with timestamps (now only with filenames match)

    if not os.path.exists(experiments_dir):
        logger.error(f"Experiment {experiments_dir} doesn't exist")
        return {}

    metrics_per_folder = {
        folder: QualityResultFolder(folder, num_videos=0, mrr=0, mp=0, recall=0, found_original=0) for folder in dict.fromkeys(query2folder.values())
    }

    for query_name in glob.glob(os.path.join(experiments_dir, "*.json")):
        # result of searching from one query
        with open(query_name, "r") as f:
            data = json.load(f)

        metrics_per_folder = process_query_results(data, ground_truth_data, query2folder, metrics_per_folder)

    for metrics in metrics_per_folder.values():
        metrics.mrr /= metrics.num_videos
        metrics.mp /= metrics.num_videos
        metrics.recall /= metrics.num_videos
        metrics.found_original /= metrics.num_videos

    return metrics_per_folder


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


def save_search_results(save_dir: str, metrics: List, metric_class: Type[Union[QualityResult, QualityResultFolder]]) -> None:
    csv_filepath = os.path.join(save_dir, "quality_metrics.csv")
    with open(csv_filepath, "w", encoding="utf-8") as f:
        csv_writer = csv.writer(f, delimiter=",")
        csv_writer.writerow(metric_class.to_csv_header())
        for result in metrics:
            csv_writer.writerow(result.to_csv())


def main() -> None:
    description = "\n".join([
        "Run quality tests on db. Try:",
        "PYTHONPATH=. python scripts/quality_process.py -i /home/superustam/jam/light_video_copy_detection/data/ -o core_dataset",
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
    parser.add_argument("-o", "--output", help="output directory to store quality results", type=str, required=True)
    parser.add_argument("-B", "--buckets", help="number of buckets (default: %(default)d)", type=int, default=1)
    parser.add_argument("-b", "--bucket", help="index of bucket (0...buckets-1, default: %(default)d)", type=int, default=0)
    args = parser.parse_args()

    input_path = args.input
    output_path = args.output

    logger = get_logger(f"{output_path}/quality_process_{args.bucket}.log", args.bucket, args.buckets)

    if not os.path.exists(input_path):
        logger.error(f"--input={input_path} doesn't exist")
        return

    os.makedirs(output_path, exist_ok=True)

    if 0 > args.bucket or args.bucket >= args.buckets:
        logger.error(f"The --bucket={args.bucket} must be 0 < --bucket < --buckets={args.buckets}")
        return

    hash_names = hash_names if args.hash == "all" else [args.hash]
    search_names = search_names if args.search == "all" else [args.search]

    # setup ground true data for quality tests
    ground_truth_data = {}
    query2folder = {}

    txt_annot = glob.glob(os.path.join(input_path, "annotation", "*.txt"))
    for txtfile in txt_annot:
        folder_name = txtfile[txtfile.rfind("/") + 1: txtfile.rfind(".")]

        with open(txtfile, "r") as list_sources:
            for row in list_sources:
                cells = row.split(",")
                if cells[0] == cells[1] and cells[2] == cells[4] and cells[3] == cells[5]:
                    continue

                cells[5] = cells[5].strip()

                k1 = (cells[0], cells[2], cells[3])
                k2 = (cells[1], cells[4], cells[5])
                ground_truth_data.setdefault(k1, []).append(k2)
                ground_truth_data.setdefault(k2, []).append(k1)
                query2folder[k1] = folder_name
                query2folder[k2] = folder_name

    # start of quality metrics calculation
    final_results: List[QualityResult] = []

    for hash_name in hash_names:
        for search_name in search_names:
            experiments_dir = os.path.join(output_path, search_name, hash_name)
            metrics_per_folder = calculate_metrics(experiments_dir, ground_truth_data, query2folder)

            save_search_results(save_dir=experiments_dir, metrics=list(metrics_per_folder.values()), metric_class=QualityResultFolder, logger=logger)
            final_results.append(QualityResult(search_name, hash_name, list(metrics_per_folder.values())))

    save_search_results(save_dir=output_path, metrics=final_results, metric_class=QualityResult)
    logger.info("Done")


if __name__ == "__main__":
    main()
