# todo: document


from typing import Any
from abc import abstractmethod

import json
import os
import wx

from ..persistent import get_last_ui_config_file_path

# todo: use dataclass

class ConfigDisplay(wx.Panel):
    def __init__(self, parent: wx.Window):
        super().__init__(parent)
    # to be used by UI objects displaying configuration
    @abstractmethod
    def restore_from_saved(self, config_objects: dict[str,Any]):
        pass

    @abstractmethod
    def get_current_displayed_config(self) -> dict[str,Any]:
        pass


class ConfigLoader:
    def __init__(self):
        self.config_displays: list[ConfigDisplay] = []

    def add_config_display(self, config_display: ConfigDisplay):
        self.config_displays.append(config_display)

    def load_saved_config(self):
        mapping_dict = self.__load_from_file()
        # todo: when loading or saving raises an exception, it should
        # log which element raised the exception and which input field
        for display in self.config_displays:
            display.restore_from_saved(mapping_dict)

    def save_current_config(self):
        mapping_dict: dict[str,Any] = {}
        # todo: when loading or saving raises an exception, it should
        # log which element raised the exception and which input field
        for display in self.config_displays:
            updated_mapping = display.get_current_displayed_config()
            mapping_dict.update(updated_mapping)

        self.__save_to_file(mapping_dict)

    def __load_from_file(self) -> dict[str,Any]:
        conf_path = get_last_ui_config_file_path()

        # if the file does not exist, create it
        if not os.path.exists(conf_path):
            with open(conf_path, 'w', encoding="utf-8"):
                pass
            return {}
        # else try to parse json
        else:
            with open(conf_path, "r", encoding="utf-8") as config_file:
                try:
                    json_data = json.load(config_file)
                    return json_data
                except json.decoder.JSONDecodeError:
                    # in case of faulty decoding, return no parsed config.
                    # it will be overwritten at coil generation anyways
                    # todo: add log here
                    return {}


    def __save_to_file(self, new_config: dict[str,Any]):
        with open(get_last_ui_config_file_path(), "w", encoding="utf-8") as config_file:
            json.dump(new_config, config_file, indent=4)
