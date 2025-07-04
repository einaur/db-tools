import subprocess
import numpy as np
from tests.utils import make_info_npz
from db_tools.main import get_db_connection


def test_update(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    prefix = str(output_dir)
    db_path = tmp_path / "output.db"

    fileroot = "run1"

    original_inputs = {"omega": 0.057, "E0": 0.01}
    make_info_npz(output_dir, fileroot, original_inputs)

    subprocess.run(["dbtools", "update", "--prefix", prefix], check=True)

    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT inputs FROM output_files WHERE filename = ?", (fileroot,))
    row = cursor.fetchone()
    assert row is not None
    inputs_in_db = eval(row[0])
    assert inputs_in_db == original_inputs
    conn.close()

    updated_inputs = {"omega": 0.057, "E0": 0.02}
    make_info_npz(output_dir, fileroot, updated_inputs)

    subprocess.run(["dbtools", "update", "--prefix", prefix], check=True)

    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT inputs FROM output_files WHERE filename = ?", (fileroot,))
    row = cursor.fetchone()
    assert row is not None
    inputs_in_db = eval(row[0])
    assert inputs_in_db == updated_inputs
    conn.close()


def test_update_with_prune(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    make_info_npz(output_dir, "run1", {"dt": 0.1})
    make_info_npz(output_dir, "run2", {"dt": 0.05})

    subprocess.run(["dbtools", "update", "--prefix", str(output_dir)], check=True)

    (output_dir / "run1_info.npz").unlink()

    subprocess.run(["dbtools", "update", "--prefix", str(output_dir)], check=True)

    result = subprocess.run(
        ["dbtools", "search", "--prefix", str(output_dir)],
        capture_output=True,
        text=True,
    )

    output = result.stdout
    assert "run1" not in output
    assert "run2" in output
