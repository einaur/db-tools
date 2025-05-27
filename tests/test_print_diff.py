import subprocess
from tests.utils import make_info_npz


def test_print_diff_outputs_only_differences(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    prefix = str(output_dir)

    inputs1 = {"omega": 0.057, "E0": 0.01, "dt": 0.05}
    inputs2 = {"omega": 0.057, "E0": 0.02, "dt": 0.05}

    make_info_npz(output_dir, "entry1", inputs1)
    make_info_npz(output_dir, "entry2", inputs2)

    subprocess.run(["dbtools", "update", "--prefix", prefix], check=True)

    result = subprocess.run(
        ["dbtools", "print_diff", "entry1", "entry2", "--prefix", prefix],
        capture_output=True,
        text=True,
        check=True,
    )

    output = result.stdout

    assert "E0" in output
    assert "dt" not in output
    assert "omega" not in output
