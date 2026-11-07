# todo: document


from abc import ABC, abstractmethod
from typing import Callable, override, Union

import wx

from wx import BitmapButton, BoxSizer, Control, FlexGridSizer, StaticText, Window
from .config_input import ConfigInputInterface
from .helper import get_default_obj_spacing

class ConfigRow(ABC):
    @abstractmethod
    def generate_name_label(self, parent: Window) -> StaticText:
        pass

    @abstractmethod
    def generate_input_field(self, parent: Window) -> Control:
        pass

    @abstractmethod
    def generate_suffix_object(self, parent: Window) -> Union[StaticText,BitmapButton]:
        pass

# todo: this is not necessary if all ui elements get created at the same time
class ButtonInputConnector:
    def __init__(self):
        self.button: Union[None,BitmapButton] = None
        self.input: Union[None,Control] = None

    def set_button(self, button: BitmapButton):
        self.button = button

    def set_input(self, input_field: Control):
        self.input = input_field

class ConfigButton:
    # icon should be one of the wx.ART_xxx numbers
    def __init__(self, icon: int, callback: Callable[[wx.Event,ButtonInputConnector],None], tooltip: Union[None,str] = None, ):
        self._icon = icon
        self._tooltip = tooltip
        self._callback = callback

    def generate_button(self, parent: Window) -> BitmapButton:
        # with wx.Button, some button bitmap IDs like wx.ID_REFRESH did not load an image
        # thats why the bitmap is now loaded manually
        bitmap = wx.ArtProvider.GetBitmap(self._icon)

        button = BitmapButton(parent, bitmap=bitmap)
        if self._tooltip is not None:
            button.SetToolTip(self._tooltip)

        return button

    def get_callback_func(self) -> Callable[[wx.Event,ButtonInputConnector],None]:
        return self._callback

class ConfigButtonRow(ConfigRow):
    def __init__(self,  name: str, input_field: ConfigInputInterface, button: ConfigButton):
        self._name = name
        self._input_field = input_field
        self._button = button
        self._button_input_connector = ButtonInputConnector()
        self._callback_execute_func = button.get_callback_func()

    @override
    def generate_name_label(self, parent: Window) -> StaticText:
        return StaticText(parent, label=self._name)

    @override
    def generate_input_field(self, parent: Window) -> Control:
        control = self._input_field.generate_control(parent)
        self._button_input_connector.set_input(control)
        return control

    @override
    def generate_suffix_object(self, parent: Window) -> Union[StaticText,BitmapButton]:
        button = self._button.generate_button(parent)
        button.Bind(wx.EVT_BUTTON, self.__button_callback)

        self._button_input_connector.set_button(button)
        return button

    # didnt find a better way to connect button and control that get generated
    # at different times than having to push through an inner callback
    def __button_callback(self, event: wx.Event):
        self._callback_execute_func(event, self._button_input_connector)


class ConfigUnitRow(ConfigRow):
    def __init__(self,  name: str, input_field: ConfigInputInterface, unit: Union[None,str]):
        self._name = name
        self._input_field = input_field
        self._unit = unit

    @override
    def generate_name_label(self, parent: Window) -> StaticText:
        return StaticText(parent, label=self._name)

    @override
    def generate_input_field(self, parent: Window) -> Control:
        return self._input_field.generate_control(parent)

    @override
    def generate_suffix_object(self, parent: Window) -> Union[StaticText,BitmapButton]:
        if self._unit is not None:
            return StaticText(parent, label=self._unit)
        else:
            return self._unit

class ConfigGrid(wx.Panel):

    def __init__(self, parent: Window, config_objects: list[ConfigRow]):
        super().__init__(parent)

        self.config_objects = config_objects
        spacing = get_default_obj_spacing()

        self.grid_sizer = FlexGridSizer(3, spacing, spacing)
        wx_alignment = wx.EXPAND | wx.ALL | wx.ALIGN_CENTER_VERTICAL

        for obj in self.config_objects:
            self.grid_sizer.Add(obj.generate_name_label(self), 0, wx_alignment, 0)
            self.grid_sizer.Add(obj.generate_input_field(self), 0, wx_alignment, 0)
            self.grid_sizer.Add(obj.generate_suffix_object(self), 0, wx_alignment, 0)

        self.SetSizer(self.grid_sizer)
        self.Fit()

    def get_current_min_row_width(self) -> (int, int, int):
        # would rather use tuple but can not since tuple does not allow member mutability
        biggest_column_width = [0, 0, 0]
        sizer_items = self.grid_sizer.GetChildren()

        for row in range(0, len(sizer_items) // 3):
            for column in range(0,3):
                item_num = row * 3 + column
                element = sizer_items[item_num]

                if biggest_column_width[column] < element.GetSize().GetWidth():
                    biggest_column_width[column] = element.GetSize().GetWidth()

        return tuple(biggest_column_width)

    def set_min_column_width(self, min_width: (int, int, int)):
        sizer_items = self.grid_sizer.GetChildren()
        for row in range(0, len(sizer_items) // 3):
            for column in range(0,3):
                item_num = row * 3 + column
                current_height = sizer_items[item_num].GetSize().GetHeight()
                sizer_items[item_num].SetMinSize(wx.Size(min_width[column], current_height))


class ConfigPanel(wx.Panel):
    def __init__(self, parent: wx.Window, config_objects: list[ConfigRow], title: str):
        super().__init__(parent)

        title = StaticText(self, label=title)
        font = title.GetFont()
        font.SetPointSize(font.GetPointSize() + 4)
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        title.SetFont(font)
        box_sizer = BoxSizer(wx.VERTICAL)
        box_sizer.Add(title, 0, wx.TOP | wx.BOTTOM, get_default_obj_spacing())
        self.config_grid = ConfigGrid(self, config_objects)
        box_sizer.Add(self.config_grid, 0, wx.TOP | wx.BOTTOM, get_default_obj_spacing())
        self.SetSizer(box_sizer)

    def get_current_min_row_width(self) -> (int, int, int):
        return self.config_grid.get_current_min_row_width()

    def set_min_column_width(self, min_width: (int, int, int)):
        self.config_grid.set_min_column_width(min_width)