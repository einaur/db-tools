import json
from db_tools.search import get_differing_keys
from db_tools.db import get_db_connection, fetch_inputs
from db_tools.utils import check_output_dir


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
