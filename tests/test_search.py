import subprocess
import json
import re
import numpy as np
from tests.utils import make_info_npz, extract_filenames


def test_search_filters(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    make_info_npz(output_dir, "run1", {"omega": 0.057, "E0": 0.01})
    make_info_npz(output_dir, "run2", {"omega": 0.057, "E0": 0.01})
    make_info_npz(output_dir, "run3", {"omega": 0.057, "E0": 0.02})

    result = subprocess.run(
        ["dbtools", "search", "--prefix", str(output_dir), "-E0", "0.01"],
        capture_output=True,
        text=True,
        check=True,
    )

    filenames = extract_filenames(result.stdout)

    assert set(filenames) == {"run1", "run2"}


def test_search_diff(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    prefix = str(output_dir)

    entries = [
        ("runA", {"omega": 0.057, "E0": 0.01, "dt": 0.05}),
        ("runB", {"omega": 0.057, "E0": 0.02, "dt": 0.05}),
        ("runC", {"omega": 0.057, "E0": 0.03, "dt": 0.05}),
    ]

    for name, inputs in entries:
        make_info_npz(output_dir, name, inputs)

    subprocess.run(["dbtools", "update", "--prefix", prefix], check=True)

    result = subprocess.run(
        [
            "dbtools",
            "search",
            "--prefix",
            prefix,
            "-omega",
            "0.057",
            "--print-style=diff",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    output = result.stdout

    diff_blocks = re.findall(r"Differing Inputs:\s*(\{.*?\})", output, re.DOTALL)
    all_keys = set()
    for block in diff_blocks:
        try:
            parsed = json.loads(block)
            all_keys.update(parsed.keys())
        except json.JSONDecodeError:
            assert False, f"Could not parse JSON block: {block}"

    assert all_keys == {"E0"}
