import json

from .config import load_input_keys


def get_search_keywords(args):
    input_keys = load_input_keys()
    return {
        key: getattr(args, key, None)
        for key in input_keys
        if getattr(args, key, None) is not None
    }


def find_filenames_by_subset_inputs(search_inputs, db_connection):
    cursor = db_connection.cursor()

    query = "SELECT filename, inputs, extra_fields FROM output_files"
    conditions = []
    params = []

    for key, value in search_inputs.items():
        conditions.append(f"json_extract(inputs, '$.{key}') = ?")
        params.append(value)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    cursor.execute(query, params)
    results = cursor.fetchall()

    matching_entries = []
    for filename, inputs_json, extra_fields_json in results:
        inputs = json.loads(inputs_json)
        extra_fields = json.loads(extra_fields_json) if extra_fields_json else {}
        if all(item in inputs.items() for item in search_inputs.items()):
            matching_entries.append((filename, inputs, extra_fields))

    return matching_entries


def get_differing_keys(entries):
    if not entries:
        return set()

    all_keys = set()
    for _, inputs, _ in entries:
        all_keys.update(inputs.keys())

    differing_keys = set()

    for key in all_keys:
        values = set()
        for _, inputs, _ in entries:
            values.add(inputs.get(key, "__MISSING__"))
        if len(values) > 1:
            differing_keys.add(key)

    return differing_keys
