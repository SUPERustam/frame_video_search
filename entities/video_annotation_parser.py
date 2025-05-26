import glob
import logging
import os
from typing import List


class VideoAnnotationParser:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

    def parse(self, annotation_path: str) -> List[str]:
        """
        Parse annotation files with removing self-duplicates
        """
        data = []
        dataset = os.path.join(annotation_path[: annotation_path[:-1].rfind("/")], "core_dataset")

        txt_annot = glob.glob(f"{annotation_path}/*")

        for txtfile in txt_annot:
            folder_name = txtfile[txtfile.rfind("/") + 1: txtfile.rfind(".")]

            with open(txtfile, "r") as list_sources:
                for row in list_sources:
                    cells = row.split(",")
                    if cells[0] == cells[1]:  # remove self-duplicates
                        continue

                    cells[0] = os.path.join(dataset, folder_name, cells[0])
                    cells[1] = os.path.join(dataset, folder_name, cells[1])
                    cells[5] = cells[5].rstrip("\n")
                    data.append((cells[0], cells[2], cells[3]))
                    data.append((cells[1], cells[4], cells[5]))

        # deduplication of video pairs
        data = list(dict.fromkeys(data))
        return data
