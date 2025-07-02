from .db import get_db_connection, fetch_inputs
from .search import find_filenames_by_subset_inputs


class DBTools:
    def __init__(self, prefix="output"):
        self.prefix = prefix
        self.base_filters = {}

    def set_base_filters(self, **kwargs):
        self.base_filters = kwargs

    def search(self, **filters):
        all_filters = self.base_filters.copy()
        all_filters.update(filters)

        db_path = f"{self.prefix}.db"
        conn = get_db_connection(db_path)
        results = find_filenames_by_subset_inputs(all_filters, conn)
        conn.close()
        return [filename for filename, inputs, _ in results]

    def get_inputs(self, fileroot):
        db_path = f"{self.prefix}.db"
        conn = get_db_connection(db_path)
        inputs = fetch_inputs(conn, fileroot)
        conn.close()
        return inputs
