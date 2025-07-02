import json
import os


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
