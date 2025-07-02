import json
import os
import numpy as np


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


def delete_output_files(output_dir, fileroot):
    deleted_files = []
    for file in os.listdir(output_dir):
        if file.startswith(fileroot):
            path = os.path.join(output_dir, file)
            try:
                os.remove(path)
                deleted_files.append(file)
            except Exception as e:
                print(f"Failed to delete {file}: {e}")
    return deleted_files
