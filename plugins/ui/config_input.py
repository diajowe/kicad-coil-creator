# todo: document

from abc import ABC, abstractmethod
from typing import Any, Callable, override, Union
from wx import Choice, Control, SpinCtrl, SpinCtrlDouble, TextCtrl, Window
from ..generator.helper_classes import ConfigValueRange, RotationDirection


class ControlAccessor:

    def __init__(self, getter: Callable[[], Any], setter: Callable[[Any], None]):
        self.get_value = getter
        self.set_value = setter


class ConfigInputInterface(ABC):
    @abstractmethod
    def generate_control(self, parent: Window) -> (Control, ControlAccessor):
        pass


class StringInput(ConfigInputInterface):

    def __init__(self, default_value: Union[None, str] = None, tooltip: Union[None, str] = None):
        super().__init__()
        self._default_value = default_value if default_value is not None else ""
        self._tooltip = tooltip
# todo: use override everywhere where applicable

    @override
    def generate_control(self, parent: Window) -> (Control, ControlAccessor):
        text_input = TextCtrl(parent)
        if self._tooltip is not None:
            text_input.SetToolTip(self._tooltip)
        if self._default_value is not None:
            text_input.SetValue(self._default_value)

        return (text_input, ControlAccessor(text_input.GetValue, text_input.SetValue))


class FloatInput(ConfigInputInterface):
    _NUM_DIGIT_FLOATING_POINT: int = 2

    def __init__(self, value_range: ConfigValueRange, default_value: Union[None, float] = None, tooltip: Union[None, str] = None):
        super().__init__()
        self._value_range = value_range
        self._default_value = default_value if default_value is not None else 0.0
        self._tooltip = tooltip

    @override
    def generate_control(self, parent: Window) -> (Control, ControlAccessor):
        float_input = SpinCtrlDouble(
            parent,
            min=self._value_range.minimum,
            max=self._value_range.maximum,
            initial=self._default_value,
            inc=0.1
            )
        float_input.SetDigits(self._NUM_DIGIT_FLOATING_POINT)
        if self._tooltip is not None:
            float_input.SetToolTip(self._tooltip)
        if self._default_value is not None:
            float_input.SetValue(self._default_value)

        return (float_input, ControlAccessor(float_input.GetValue, float_input.SetValue))


class IntInput(ConfigInputInterface):
    def __init__(self, value_range: ConfigValueRange, default_value: Union[None, int] = None, tooltip: Union[None, str] = None):
        super().__init__()
        self._value_range = value_range
        self._default_value = default_value
        self._tooltip = tooltip

    @override
    def generate_control(self, parent: Window) -> (Control, ControlAccessor):
        int_input = SpinCtrl(
            parent,
            min=self._value_range.minimum,
            max=self._value_range.maximum,
            initial=self._default_value
            )
        if self._tooltip is not None:
            int_input.SetToolTip(self._tooltip)
        if self._default_value is not None:
            int_input.SetValue(self._default_value)

        return (int_input, ControlAccessor(int_input.GetValue, int_input.SetValue))


class RotationDirectionInput(ConfigInputInterface):
    def __init__(self, default_value: Union[None, RotationDirection] = None, tooltip: Union[None, str] = None):
        super().__init__()
        self._default_value = default_value
        self._tooltip = tooltip

    @override
    def generate_control(self, parent: Window) -> (Control, ControlAccessor):
        direction_input = Choice(parent)
        for direction in RotationDirection:
            direction_input.Append(
                RotationDirectionInput.rotation_direction_to_string_value(
                    direction),
                direction
            )
        direction_input.SetSelection(self._default_value.value)
        if self._tooltip is not None:
            direction_input.SetToolTip(self._tooltip)

        return (direction_input, ControlAccessor(direction_input.GetSelection, direction_input.SetSelection))

    @classmethod
    def rotation_direction_to_string_value(cls, rotation_direction: RotationDirection) -> str:
        variant_name = rotation_direction.name
        variant_split = variant_name.split("_")
        for index, part in enumerate(variant_split):
            variant_split[index] = part.capitalize()
        return "".join(variant_split)
