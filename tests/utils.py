import re
from pathlib import Path
import numpy as np


def make_info_npz(path: Path, fileroot: str, inputs: dict):
    filename = path / f"{fileroot}_info.npz"
    np.savez(filename, inputs=inputs)
    return filename


def extract_filenames(output):
    return [match.rstrip(",") for match in re.findall(r"Filename:\s*(\S+)", output)]
