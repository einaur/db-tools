import argparse
import os


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
