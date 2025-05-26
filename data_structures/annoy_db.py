from dataclasses import dataclass

import annoy


@dataclass
class AnnoyDB:
    db_index: list[list]
    annoy_index: annoy.AnnoyIndex
