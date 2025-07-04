import subprocess
import os
import numpy as np


from db_tools.main import (
    get_db_connection,
    create_table_if_not_exists,
    add_entry_to_database,
)


def test_delete(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    prefix = str(tmp_path / "output")

    fileroot = "testfile"
    info_path = output_dir / f"{fileroot}_info.npz"
    samples_path = output_dir / f"{fileroot}_samples.npz"

    np.savez(info_path, inputs={"omega": 0.057, "dt": 0.05})
    np.savez(samples_path, samples=np.array([1, 2, 3]))

    db_path = os.path.join(prefix, "dbtools.db")
    conn = get_db_connection(db_path)
    create_table_if_not_exists(conn)
    add_entry_to_database(conn, fileroot, {"omega": 0.057, "dt": 0.05}, None)
    conn.close()

    subprocess.run(
        ["dbtools", "delete", fileroot, "--prefix", str(output_dir), "--force"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert not info_path.exists()
    assert not samples_path.exists()

    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM output_files WHERE filename = ?", (fileroot,))
    assert cursor.fetchone() is None
    conn.close()
