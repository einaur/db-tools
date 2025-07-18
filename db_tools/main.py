import argparse
import os
import numpy as np
import sys

from .db import (
    get_db_connection,
    create_table_if_not_exists,
    ensure_extra_fields_column,
    add_entry_to_database,
    count_entries,
    delete_db_entry,
)

from .io import (
    load_info_file,
    delete_output_files,
)

from .search import (
    get_search_keywords,
    find_filenames_by_subset_inputs,
)

from .print import (
    print_db_results,
    print_entry,
    print_diff,
)

from .config import load_input_keys, load_search_config
from .utils import check_output_dir, TYPE_MAP


def update(prefix, prune=True, fast=False):
    if not check_output_dir(prefix):
        return

    output_dir = f"{prefix}/"
    db_path = os.path.join(prefix, "dbtools.db")

    conn = get_db_connection(db_path)
    create_table_if_not_exists(conn)
    ensure_extra_fields_column(conn)

    cursor = conn.cursor()

    if fast:
        cursor.execute("SELECT filename, mtime FROM output_files")
        db_mtimes = dict(cursor.fetchall())
    else:
        db_mtimes = {}

    seen_filenames = set()

    for file in os.listdir(output_dir):
        if file.endswith("_info.npz") or file.endswith("_info.json"):
            filename = file.replace("_info.npz", "").replace("_info.json", "")
            seen_filenames.add(filename)

            file_path = os.path.join(output_dir, file)
            current_mtime = os.path.getmtime(file_path)

            if fast and filename in db_mtimes:
                db_mtime = db_mtimes[filename]
                if abs(db_mtime - current_mtime) < 1e-6:
                    continue

            try:
                inputs, extra_fields = load_info_file(file_path)
                add_entry_to_database(
                    conn, filename, inputs, extra_fields, current_mtime
                )
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

    db_path = os.path.join(prefix, "dbtools.db")
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

    deleted_files = delete_output_files(output_dir, entry_name)
    conn = get_db_connection(db_path)
    delete_db_entry(conn, entry_name)
    conn.close()

    print("Deleted database entry.")
    if deleted_files:
        print("Deleted files:")
        for file in deleted_files:
            print(f" - {file}")
    else:
        print("No files deleted.")


def number(prefix):
    db_path = os.path.join(prefix, "dbtools.db")
    conn = get_db_connection(db_path)
    num_entries = count_entries(conn)
    conn.close()
    print(f"Number of entries in the database: {num_entries}")


def search(prefix, args):
    if not check_output_dir(prefix):
        return []

    db_path = os.path.join(prefix, "dbtools.db")
    conn = get_db_connection(db_path)

    search_keywords = get_search_keywords(args)

    entries = find_filenames_by_subset_inputs(search_keywords, conn)

    conn.close()

    return entries


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


def parse_search(parser):
    input_keys = load_input_keys()

    for key, typestr in input_keys.items():
        if typestr not in TYPE_MAP:
            print(f"ERROR: Unsupported type '{typestr}' for key '{key}'.")
            print("       Supported types are:", ", ".join(TYPE_MAP.keys()))
            print("       Please fix this in your dbtools.inputs.json or .append.json.")
            sys.exit(1)

        parser.add_argument(f"-{key}", type=TYPE_MAP[typestr], help=argparse.SUPPRESS)


def add_prefix(parser):
    parser.add_argument(
        "--prefix",
        type=str,
        default="output",
        help="Name of output directory and prefix for .db file",
    )


def add_print_options(parser):
    parser.add_argument(
        "--print-style",
        choices=["names", "brief", "full", "diff"],
        default="full",
        help="Style of output formatting",
    )

    parser.add_argument(
        "--show-field",
        action="append",
        default=[],
        help="Show extra field(s) (e.g., metadata, timings, extra_field) in printouts if present",
    )


def add_update_options(parser):
    parser.add_argument(
        "--no-prune",
        action="store_true",
        help="Do not remove database entries for missing output files",
    )

    parser.add_argument(
        "--fast", action="store_true", help="Skip files already present in the database"
    )


def add_auto_update_options(parser):
    parser.add_argument(
        "--no-update",
        action="store_true",
        help="Skip automatic update --fast before running this command",
    )

    parser.add_argument(
        "--no-prune",
        action="store_true",
        help="Do not remove database entries for missing output files",
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

    # number
    parser_number = subparsers.add_parser(
        "number", aliases=["n"], help="Print number of entries in database"
    )

    add_prefix(parser_number)
    add_auto_update_options(parser_number)

    # print
    parser_print = subparsers.add_parser(
        "print", aliases=["p"], help="Print all database entries"
    )

    add_prefix(parser_print)
    add_auto_update_options(parser_print)
    add_print_options(parser_print)

    # print_entry
    parser_print_entry = subparsers.add_parser(
        "print_entry", aliases=["pe"], help="Print a single database entry"
    )

    add_prefix(parser_print_entry)
    add_auto_update_options(parser_print_entry)
    add_print_options(parser_print_entry)

    parser_print_entry.add_argument("entry_name", type=str)

    # print_diff
    parser_print_diff = subparsers.add_parser(
        "print_diff",
        aliases=["pd", "diff"],
        help="Print differing inputs between two entries",
    )

    add_prefix(parser_print_diff)
    add_auto_update_options(parser_print_diff)

    parser_print_diff.add_argument("entry1", type=str)
    parser_print_diff.add_argument("entry2", type=str)
    parser_print_diff.add_argument("-name", type=str, default="output")

    parser_print_diff.add_argument(
        "--style",
        choices=["horizontal", "vertical"],
        default="horizontal",
        help="Format of the comparison output",
    )

    # search
    parser_search = subparsers.add_parser(
        "search", aliases=["s"], help="Search for entries matching input subset"
    )

    add_prefix(parser_search)
    add_auto_update_options(parser_search)
    parse_search(parser_search)
    add_print_options(parser_search)

    parser_search.add_argument(
        "--search-config",
        type=str,
        help="Name of a predefined search config (from search_config.json or search_config.replace.json)",
    )

    # update
    parser_update = subparsers.add_parser(
        "update", aliases=["u"], help="Scan output directory and update database."
    )

    add_prefix(parser_update)
    add_update_options(parser_update)

    # delete
    parser_delete = subparsers.add_parser(
        "delete", aliases=["d"], help="Delete database entry and related output files"
    )

    add_prefix(parser_delete)

    parser_delete.add_argument(
        "entry_name", type=str, help="Name of the output entry to delete"
    )

    parser_delete.add_argument(
        "--force", action="store_true", help="Delete without confirmation"
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


def fast_update_if_needed(args):
    if not getattr(args, "no_update", False):
        update(args.prefix, prune=not args.no_prune, fast=True)


def main():
    args = setup_parser()

    if not check_output_dir(args.prefix):
        return

    if args.action in {"number", "print", "print_entry", "print_diff", "search"}:
        fast_update_if_needed(args)

    if args.action == "number":
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

    elif args.action == "print_diff":
        print_diff(args.prefix, args.entry1, args.entry2, style=args.style)

    elif args.action == "search":
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

    elif args.action == "update":
        update(args.prefix, prune=not args.no_prune, fast=args.fast)

    elif args.action == "delete":
        delete(args.prefix, args.entry_name, force=args.force)


if __name__ == "__main__":
    main()
