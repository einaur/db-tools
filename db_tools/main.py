import argparse
import os
import sqlite3
import numpy as np
import json
import sys


def get_db_connection(db_path, timeout=300):
    return sqlite3.connect(db_path, timeout=timeout)


def create_table_if_not_exists(conn):
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS output_files (
            id INTEGER PRIMARY KEY,
            filename TEXT NOT NULL UNIQUE,
            inputs TEXT NOT NULL,
            extra_fields TEXT
        )
        """
    )
    conn.commit()


def ensure_extra_fields_column(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(output_files)")
    columns = [row[1] for row in cursor.fetchall()]
    if "extra_fields" not in columns:
        cursor.execute("ALTER TABLE output_files ADD COLUMN extra_fields TEXT")
        conn.commit()


def add_entry_to_database(conn, filename, inputs, extra_fields):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO output_files (filename, inputs, extra_fields) VALUES (?, ?, ?)",
        (
            filename,
            json.dumps(inputs),
            json.dumps(extra_fields) if extra_fields else None,
        ),
    )
    conn.commit()


def fetch_inputs(conn, filename):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT inputs, extra_fields FROM output_files WHERE filename = ?", (filename,)
    )
    result = cursor.fetchone()
    if result:
        inputs = json.loads(result[0])
        extra_fields = json.loads(result[1]) if result[1] else {}
        return inputs, extra_fields
    return None, None


def load_config(basename):
    config_name = f"{basename}.json"
    replace_name = f"{basename}.replace.json"

    cwd = os.getcwd()
    config_home = os.path.expanduser("~/.config/dbtools")
    install_dir = os.path.dirname(__file__)

    replace_paths = [
        os.path.join(cwd, "dbtools." + replace_name),
        os.path.join(config_home, replace_name),
    ]

    for path in replace_paths:
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)

    config = {}
    for path in [
        os.path.join(install_dir, "dbtools." + config_name),
        os.path.join(config_home, config_name),
        os.path.join(cwd, "dbtools." + config_name),
    ]:
        if os.path.exists(path):
            with open(path) as f:
                config.update(json.load(f))

    return config


def load_input_keys():
    return load_config("inputs")


def load_search_config():
    return load_config("search_config")


def str2bool(val):
    if val is None or val == "":
        return False
    val = val.strip().lower()
    if val in ("1", "true", "yes"):
        return True
    elif val in ("0", "false", "no"):
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean value: '{val}'")


TYPE_MAP = {"str": str, "int": int, "float": float, "bool": str2bool}


def check_output_dir(prefix):
    output_dir = f"{prefix}/"
    if not os.path.isdir(output_dir):
        print(f"Error: Output directory '{output_dir}' does not exist.")
        return False
    return True


def load_info_file(file_path):
    if file_path.endswith(".npz"):
        data = np.load(file_path, allow_pickle=True)
        inputs = data["inputs"].item()
        extra_fields = {}
        for k in data.files:
            if k == "inputs":
                continue
            try:
                v = data[k].item()
            except Exception:
                v = data[k]
            extra_fields[k] = v
        return inputs, extra_fields
    elif file_path.endswith(".json"):
        with open(file_path, "r") as f:
            data = json.load(f)
        inputs = data.get("inputs", {})
        extra_fields = {k: v for k, v in data.items() if k != "inputs"}
        return inputs, extra_fields
    else:
        raise ValueError(f"Unsupported file format: {file_path}")


def update(prefix, prune=False, fast=False):
    if not check_output_dir(prefix):
        return

    output_dir = f"{prefix}/"
    db_path = f"{prefix}.db"

    conn = get_db_connection(db_path)
    create_table_if_not_exists(conn)
    ensure_extra_fields_column(conn)

    cursor = conn.cursor()

    existing_filenames = set()
    if fast:
        cursor.execute("SELECT filename FROM output_files")
        existing_filenames = {row[0] for row in cursor.fetchall()}

    seen_filenames = set()

    for file in os.listdir(output_dir):
        if file.endswith("_info.npz") or file.endswith("_info.json"):
            filename = file.replace("_info.npz", "").replace("_info.json", "")
            seen_filenames.add(filename)

            if fast and filename in existing_filenames:
                continue

            file_path = os.path.join(output_dir, file)
            try:
                inputs, extra_fields = load_info_file(file_path)
                add_entry_to_database(conn, filename, inputs, extra_fields)
            except Exception as e:
                print(f"Failed to process file {file_path}: {e}")

    if prune:
        cursor.execute("SELECT filename FROM output_files")
        db_filenames = {row[0] for row in cursor.fetchall()}

        missing = db_filenames - seen_filenames
        for filename in missing:
            print(f"Pruning missing file: {filename}")
            cursor.execute("DELETE FROM output_files WHERE filename = ?", (filename,))
        conn.commit()

    conn.close()


def delete(prefix, entry_name, force=False):
    if not check_output_dir(prefix):
        return

    db_path = f"{prefix}.db"
    output_dir = f"{prefix}/"

    if not force:
        print(
            f"WARNING: This will permanently delete all files matching '{entry_name}*' in '{output_dir}'"
        )
        print(f"and remove the entry from the database '{db_path}'.")
        confirm = input("Are you sure? Type 'yes' to confirm: ")

        if confirm.strip().lower() != "yes":
            print("Aborted.")
            return

    deleted_files = []
    for file in os.listdir(output_dir):
        if file.startswith(entry_name):
            path = os.path.join(output_dir, file)
            try:
                os.remove(path)
                deleted_files.append(file)
            except Exception as e:
                print(f"Failed to delete {file}: {e}")

    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM output_files WHERE filename = ?", (entry_name,))
    conn.commit()
    conn.close()

    print("Deleted database entry.")
    if deleted_files:
        print("Deleted files:")
        for file in deleted_files:
            print(f" - {file}")
    else:
        print("No files deleted.")


def count_entries(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM output_files")
    result = cursor.fetchone()
    return result[0] if result else 0


def number(prefix):
    db_path = f"{prefix}.db"
    conn = get_db_connection(db_path)
    num_entries = count_entries(conn)
    conn.close()
    print(f"Number of entries in the database: {num_entries}")


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


def search(prefix, args):
    if not check_output_dir(prefix):
        return []

    db_path = f"{prefix}.db"
    conn = get_db_connection(db_path)

    search_keywords = get_search_keywords(args)

    entries = find_filenames_by_subset_inputs(search_keywords, conn)

    conn.close()

    return entries


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


def format_entry(
    index,
    filename,
    inputs,
    print_style,
    differing_keys=None,
    print_keys=None,
    extra_field=None,
    show_fields=None,
):
    if print_keys is not None:
        inputs = {k: v for k, v in inputs.items() if k in print_keys}

    if print_style == "names":
        out = filename
    elif print_style == "brief":
        out = f"{index} Filename: {filename}"
    elif print_style == "diff":
        if differing_keys is None:
            out = f"{index} Filename: {filename}  (diff keys missing)"
        else:
            diff_inputs = {key: inputs.get(key, "<missing>") for key in differing_keys}
            out = f"{index} Filename: {filename}  Differing Inputs: {json.dumps(diff_inputs, indent=2)}"
    else:
        out = f"{index} Filename: {filename}  Inputs: {json.dumps(inputs, indent=2)}"

    if show_fields and extra_field:
        for field in show_fields:
            if field in extra_field:
                val = extra_field[field]
                if isinstance(val, dict):
                    out += f"\n{field}:\n" + json.dumps(val, indent=2)
                else:
                    out += f"\n{field}: {val}"

    return out


def print_db_results(entries, print_style="full", print_keys=None, show_field=None):
    differing_keys = None
    if print_style == "diff":
        differing_keys = get_differing_keys(entries)

    if entries:
        print("Matching entries:")
        for i, (filename, inputs, extra_fields) in enumerate(entries):
            print(
                format_entry(
                    i,
                    filename,
                    inputs,
                    print_style,
                    differing_keys,
                    print_keys,
                    extra_field=extra_fields,
                    show_fields=show_field,
                )
            )
    else:
        print("No matching records found.")
    print("Number of matching records:", len(entries))


def print_entry(prefix, filename, print_style="full", show_field=None):
    if not check_output_dir(prefix):
        return

    db_path = f"{prefix}.db"
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT inputs, extra_fields FROM output_files WHERE filename = ?", (filename,)
    )
    result = cursor.fetchone()
    conn.close()

    if result:
        inputs = json.loads(result[0])
        extra_field = json.loads(result[1]) if result[1] else {}
        print(
            format_entry(
                0,
                filename,
                inputs,
                print_style,
                extra_field=extra_field,
                show_fields=show_field,
            )
        )
    else:
        print(f"No record found for filename '{filename}'.")


def format_diff_horizontal(entry1, entry2, inputs1, inputs2):
    differing_keys = sorted(set(inputs1.keys()) | set(inputs2.keys()))
    rows = []

    for key in differing_keys:
        val1 = inputs1.get(key, "<missing>")
        val2 = inputs2.get(key, "<missing>")
        if val1 != val2:
            rows.append((key, str(val1), str(val2)))

    if not rows:
        return "No differences found."

    key_width = max(len("Key"), max(len(k) for k, _, _ in rows))
    val1_width = max(len(entry1), max(len(v1) for _, v1, _ in rows))
    val2_width = max(len(entry2), max(len(v2) for _, _, v2 in rows))

    header = (
        f"{'Key'.ljust(key_width)}   "
        f"{entry1.ljust(val1_width)}   "
        f"{entry2.ljust(val2_width)}"
    )
    separator = "-" * (key_width + val1_width + val2_width + 6)
    lines = [header, separator]

    for key, val1, val2 in rows:
        lines.append(
            f"{key.ljust(key_width)}   "
            f"{val1.ljust(val1_width)}   "
            f"{val2.ljust(val2_width)}"
        )

    return "\n".join(lines)


def format_diff_vertical(entry1, entry2, inputs1, inputs2):
    all_keys = set(inputs1.keys()) | set(inputs2.keys())
    diff = {}

    for key in all_keys:
        val1 = inputs1.get(key, "<missing>")
        val2 = inputs2.get(key, "<missing>")
        if val1 != val2:
            diff[key] = (val1, val2)

    if not diff:
        return "No differing parameters between the two entries."

    lines = ["Differences:"]
    for key, (v1, v2) in diff.items():
        lines.append(f"- {key}:\n    [1] = {v1}\n    [2] = {v2}")

    lines.append("\nFilenames:")
    lines.append(f"[1]: {entry1}")
    lines.append(f"[2]: {entry2}")
    return "\n".join(lines)


def print_diff(prefix, entry1, entry2, style="horizontal"):
    if not check_output_dir(prefix):
        return

    db_path = f"{prefix}.db"
    conn = get_db_connection(db_path)
    inputs1, extra_fields1 = fetch_inputs(conn, entry1)
    inputs2, extra_fields2 = fetch_inputs(conn, entry2)
    conn.close()

    if not inputs1 or not inputs2:
        print("Error: One or both entries not found in database.")
        return

    if style == "horizontal":
        print(format_diff_horizontal(entry1, entry2, inputs1, inputs2))
    else:
        print(format_diff_vertical(entry1, entry2, inputs1, inputs2))


def parse_search(parser):
    input_keys = load_input_keys()

    for key, typestr in input_keys.items():
        if typestr not in TYPE_MAP:
            print(f"ERROR: Unsupported type '{typestr}' for key '{key}'.")
            print("       Supported types are:", ", ".join(TYPE_MAP.keys()))
            print("       Please fix this in your dbtools.inputs.json or .append.json.")
            sys.exit(1)

        parser.add_argument(f"-{key}", type=TYPE_MAP[typestr], help=argparse.SUPPRESS)


def add_print_options(parser):
    group = parser.add_argument_group("output options")
    group.add_argument(
        "--print-style",
        choices=["names", "brief", "full", "diff"],
        default="full",
        help="Style of output formatting",
    )


def setup_parser():
    parser = argparse.ArgumentParser(
        description="dbtools: manage simulation output files and metadata stored in SQLite databases.\n\nRun 'dbtools <command> --help' to see command-specific options."
    )

    subparsers = parser.add_subparsers(
        dest="action",
        required=True,
        metavar="{update|print|print_entry|print_diff|number|search|delete}",
    )

    parser_update = subparsers.add_parser(
        "update", aliases=["u"], help="Scan output directory and update database."
    )
    parser_update.add_argument(
        "--prefix",
        type=str,
        default="output",
        help="Name of output directory and prefix for .db file",
    )
    parser_update.add_argument(
        "--prune",
        action="store_true",
        help="Remove database entries for missing output files",
    )
    parser_update.add_argument(
        "--fast", action="store_true", help="Skip files already present in the database"
    )

    parser_print = subparsers.add_parser(
        "print", aliases=["p"], help="Print all database entries"
    )
    parser_print.add_argument(
        "--prefix",
        type=str,
        default="output",
        help="Name of output directory and prefix for .db file",
    )
    add_print_options(parser_print)
    parser_print.add_argument(
        "--show-field",
        action="append",
        default=[],
        help="Show extra field(s) (e.g., metadata, timings, extra_field) in printouts if present",
    )

    parser_print_entry = subparsers.add_parser(
        "print_entry", aliases=["pe"], help="Print a single database entry"
    )
    parser_print_entry.add_argument("entry_name", type=str)
    parser_print_entry.add_argument(
        "--prefix",
        type=str,
        default="output",
        help="Name of output directory and prefix for .db file",
    )
    parser_print_entry.add_argument(
        "--print-style",
        choices=["names", "brief", "full", "diff"],
        default="full",
        help="Style of output formatting",
    )
    parser_print_entry.add_argument(
        "--show-field",
        action="append",
        default=[],
        help="Show extra field(s) (e.g., metadata, timings, extra_field) in printouts if present",
    )

    parser_print_diff = subparsers.add_parser(
        "print_diff",
        aliases=["pd", "diff"],
        help="Print differing inputs between two entries",
    )
    parser_print_diff.add_argument("entry1", type=str)
    parser_print_diff.add_argument("entry2", type=str)
    parser_print_diff.add_argument("-name", type=str, default="output")
    parser_print_diff.add_argument(
        "--prefix",
        type=str,
        default="output",
        help="Name of output directory and prefix for .db file",
    )
    parser_print_diff.add_argument(
        "--style",
        choices=["horizontal", "vertical"],
        default="horizontal",
        help="Format of the comparison output",
    )

    parser_number = subparsers.add_parser(
        "number", aliases=["n"], help="Print number of entries in database"
    )
    parser_number.add_argument(
        "--prefix",
        type=str,
        default="output",
        help="Name of output directory and prefix for .db file",
    )

    parser_search = subparsers.add_parser(
        "search", aliases=["s"], help="Search for entries matching input subset"
    )
    parser_search.add_argument(
        "--no-update",
        action="store_true",
        help="Skip automatic update --fast before searching",
    )
    parser_search.add_argument(
        "--prefix",
        type=str,
        default="output",
        help="Name of output directory and prefix for .db file",
    )
    parser_search.add_argument(
        "--search-config",
        type=str,
        help="Name of a predefined search config (from search_config.json or search_config.replace.json)",
    )
    parser_search.add_argument(
        "--show-field",
        action="append",
        default=[],
        help="Show extra field(s) (e.g., metadata, timings, extra_field) in printouts if present",
    )

    parse_search(parser_search)
    add_print_options(parser_search)

    parser_delete = subparsers.add_parser(
        "delete", aliases=["d"], help="Delete database entry and related output files"
    )
    parser_delete.add_argument(
        "entry_name", type=str, help="Name of the output entry to delete"
    )
    parser_delete.add_argument(
        "--force", action="store_true", help="Delete without confirmation"
    )
    parser_delete.add_argument(
        "--prefix",
        type=str,
        default="output",
        help="Database name/output directory prefix",
    )

    args = parser.parse_args()

    alias_map = {
        "s": "search",
        "u": "update",
        "p": "print",
        "pe": "print_entry",
        "pd": "print_diff",
        "diff": "print_diff",
        "d": "delete",
        "n": "number",
    }

    if args.action in alias_map:
        args.action = alias_map[args.action]

    return args


def apply_search_config(args, search_configs):
    config = search_configs.get(args.search_config)
    if config is None:
        print(f"Error: search_config '{args.search_config}' not found.")
        return False

    for k, v in config.get("filters", {}).items():
        setattr(args, k, v)
    if "print_keys" in config:
        args.print_keys = config["print_keys"]
    return True


def main():
    args = setup_parser()

    if not check_output_dir(args.prefix):
        return

    if args.action == "update":
        update(args.prefix, prune=args.prune, fast=args.fast)
    elif args.action == "number":
        number(args.prefix)
    elif args.action == "print":
        entries = search(args.prefix, argparse.Namespace())
        print_db_results(
            entries, print_style=args.print_style, show_field=args.show_field
        )
    elif args.action == "print_entry":
        print_entry(
            args.prefix, args.entry_name, args.print_style, show_field=args.show_field
        )
    elif args.action == "search":
        if not args.no_update:
            update(args.prefix, fast=True)

        if getattr(args, "search_config", None):
            search_configs = load_search_config()
            if not apply_search_config(args, search_configs):
                return

        entries = search(args.prefix, args)
        print_db_results(
            entries,
            print_style=args.print_style,
            print_keys=getattr(args, "print_keys", None),
            show_field=args.show_field,
        )
    elif args.action == "print_diff":
        print_diff(args.prefix, args.entry1, args.entry2, style=args.style)
    elif args.action == "delete":
        delete(args.prefix, args.entry_name, force=args.force)


if __name__ == "__main__":
    main()
