# todo: document

from os import path
import sys

def get_persistent_base_path() -> str:
    return path.join(path.dirname(__file__), "../dynamic/")

def get_last_ui_config_file_path() -> str:
    return path.join(get_persistent_base_path(), "lastconfig.json")

def get_log_file_path() -> str:
    return path.join(get_persistent_base_path(), "coilgenerator.log")
