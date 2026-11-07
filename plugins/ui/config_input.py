# todo: document

from abc import ABC, abstractmethod
from typing import override, Union
from wx import Choice, Control, SpinCtrl, SpinCtrlDouble, TextCtrl, Window
from ..generator.helper_classes import RotationDirection

class ConfigInputInterface(ABC):
    @abstractmethod
    def generate_control(self, parent: Window) -> Control:
        pass

class StringInput(ConfigInputInterface):

    def __init__(self, default_value: Union[None,str] = None, tooltip: Union[None,str] = None):
        super().__init__()
        self._default_value = default_value
        self._tooltip = tooltip
#todo: use override everywhere where applicable
    @override
    def generate_control(self, parent: Window) -> Control:
        text_input = TextCtrl(parent)
        if self._tooltip is not None:
            text_input.SetToolTip(self._tooltip)
        if self._default_value is not None:
            text_input.SetValue(self._default_value)

        return text_input

class FloatInput(ConfigInputInterface):
    _NUM_DIGIT_FLOATING_POINT: int = 2
    # todo: load default values from default file
    _DEFAULT_INPUT_VALUE: float = 0.0

    def __init__(self, default_value: Union[None,float] = None, tooltip: Union[None,str] = None):
        super().__init__()
        self._default_value = default_value
        self._tooltip = tooltip

    @override
    def generate_control(self, parent: Window) -> Control:
        # todo: restrict input values to range
        float_input = SpinCtrlDouble(parent, min=-2**31, max=2**31 - 1, initial=self._DEFAULT_INPUT_VALUE, inc=0.1)
        float_input.SetDigits(self._NUM_DIGIT_FLOATING_POINT)
        if self._tooltip is not None:
            float_input.SetToolTip(self._tooltip)
        if self._default_value is not None:
            float_input.SetValue(self._default_value)

        return float_input

class IntInput(ConfigInputInterface):
    # todo: load default values from default file
    _DEFAULT_INPUT_VALUE: int = 0

    def __init__(self, default_value: Union[None,int] = None, tooltip: Union[None,str] = None):
        super().__init__()
        self._default_value = default_value
        self._tooltip = tooltip

    @override
    def generate_control(self, parent: Window) -> Control:
        # todo: restrict input values to range
        int_input = SpinCtrl(parent, min=-2**31, max=2**31 - 1, initial=self._DEFAULT_INPUT_VALUE)
        if self._tooltip is not None:
            int_input.SetToolTip(self._tooltip)
        if self._default_value is not None:
            int_input.SetValue(self._default_value)
        return int_input

class RotationDirectionInput(ConfigInputInterface):
    # todo: load default values from default file
    _DEFAULT_INPUT_VALUE: RotationDirection = RotationDirection.CLOCKWISE

    def __init__(self, default_value: Union[None,RotationDirection] = None, tooltip: Union[None,str] = None):
        super().__init__()
        self._default_value = default_value
        self._tooltip = tooltip

    @override
    def generate_control(self, parent: Window) -> Control:
        direction_input = Choice(parent)
        for direction in RotationDirection:
            direction_input.Append(
                RotationDirectionInput.rotation_direction_to_string_value(direction),
                direction
            )
        direction_input.SetSelection(0)
        if self._tooltip is not None:
            direction_input.SetToolTip(self._tooltip)
        return direction_input

    @classmethod
    def rotation_direction_to_string_value(cls, rotation_direction: RotationDirection) -> str:
        variant_name = rotation_direction.name
        variant_split = variant_name.split("_")
        for index, part in enumerate(variant_split):
            variant_split[index] = part.capitalize()
        return "".join(variant_split)
