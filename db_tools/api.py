import os
from .db import get_db_connection, fetch_inputs
from .main import update as update_database
from .search import find_filenames_by_subset_inputs

from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class DBTools:
    prefix: str = field(default="output")
    base_filters: dict[str, str] = field(default_factory=dict)
    fileroots: list[str] = field(default_factory=list)

    def with_prefix(self, prefix):
        return replace(self, prefix=prefix)

    def with_base_filters(self, **base_filters):
        return replace(self, base_filters=base_filters)

    def with_fileroots(self, fileroots):
        return replace(self, fileroots=fileroots)

    def search(self, update=True, **filters):
        if update:
            update_database(self.prefix, prune=True, fast=True)

        all_filters = self.base_filters.copy()
        all_filters.update(filters)

        db_path = os.path.join(self.prefix, "dbtools.db")
        conn = get_db_connection(db_path)
        results = find_filenames_by_subset_inputs(all_filters, conn)
        conn.close()
        fileroots = [fileroot for fileroot, _, _ in results]

        return replace(self, fileroots=fileroots)

    def get_inputs(self, fileroot):
        db_path = os.path.join(self.prefix, "dbtools.db")
        conn = get_db_connection(db_path)
        inputs = fetch_inputs(conn, fileroot)
        conn.close()
        return inputs

    def load(self):
        raise NotImplementedError
