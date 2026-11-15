
import os
import logging
import traceback

from .persistent import get_log_file_path

def init_logger():
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.DEBUG)

    handler = logging.FileHandler(get_log_file_path())
    handler.setLevel(logging.DEBUG)


    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d -> %(message)s", datefmt="%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)

try:
    init_logger()
    logger = logging.getLogger()
    logger.log(logging.DEBUG, "Running Coil Generator")
    from .plugin import Plugin
    plugin = Plugin()
    plugin.register()
    
    
except Exception as e:
    logger = logging.getLogger()
    logger.debug(repr(e))
    logger.debug(traceback.format_exc())

