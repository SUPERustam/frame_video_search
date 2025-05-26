import glob
import json
import logging
import os

from annoy import AnnoyIndex
from data_structures.annoy_db import AnnoyDB
from frame_hashers.abstract_frame_hasher import AbstractFrameHasher


class AnnoyProcessor:
    def __init__(self, hasher: AbstractFrameHasher, logger: logging.Logger, bucket: int, threads: int) -> None:
        self.hasher = hasher
        self.logger = logger
        self.bucket = bucket
        self.threads = threads
        self.annoy_index = None
        self.db_index = []

    def annoy_init(self) -> None:
        self.annoy_index = AnnoyIndex(self.hasher.vector_size, "euclidean")
        self.annoy_index.set_seed(42)

    def index_json(self, json_path: str, annoy_indexing: bool = False) -> None:
        with open(json_path, "r") as f:
            data = json.load(f)

        for i, frame in enumerate(data["frames"]):
            if annoy_indexing:
                self.annoy_index.add_item(len(self.db_index), frame["vec"])

            self.db_index.append([data["filename"], i, frame["timecode"]])

    def json_indexing(self, hashes_path: str, annoy_indexing: bool = False) -> None:
        json_paths = glob.glob(os.path.join(hashes_path, "*.json"))

        for json_path in json_paths:
            self.index_json(json_path, annoy_indexing)

    def build_and_save_annoy_index(self, save_dir: str) -> None:
        self.annoy_index.build(1000, n_jobs=self.threads)
        self.annoy_index.save(os.path.join(save_dir, "annoy_index.ann"))

    def load_annoy_index(self, hashes_path: str) -> None:
        self.annoy_index.load(os.path.join(hashes_path, "annoy_index.ann"))

    def load_annoy_db_from_disk(self, hashes_path: str) -> AnnoyDB:
        self.annoy_init()
        self.json_indexing(hashes_path)
        self.load_annoy_index(hashes_path)

        return AnnoyDB(db_index=self.db_index, annoy_index=self.annoy_index)

    def create_annoy_db(self, hashes_path: str) -> AnnoyDB:
        self.annoy_init()
        self.json_indexing(hashes_path, annoy_indexing=True)
        self.build_and_save_annoy_index(hashes_path)

        return AnnoyDB(db_index=self.db_index, annoy_index=self.annoy_index)
