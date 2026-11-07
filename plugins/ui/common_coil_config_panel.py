"""
Copyright (C) 2022 Colton Baldridge
Copyright (C) 2023 Tim Goll, Jonas Wenner

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

-----------------------------------------------------------------

This file is intended to provide a ui element for generator's CommonCoilConfig.
This allows the usage as WX element and helps building the coil generator's UI.
"""

# todo: document

from wx import Window

from .config_panel import ConfigPanel, ConfigUnitRow
from .config_input import IntInput, FloatInput, RotationDirectionInput


class CommonCoilConfigPanel(ConfigPanel):
    SECTION_TITLE: str = "Common Coil Configuration"
    OUTER_DIAM_LABEL_NAME: str = "Max Outer Diameter"
    OUTER_DIAM_UNIT_NAME: str = "mm"
    ROTATION_DIRECTION_LABEL_NAME: str = "Rotation Direction"
    TURNS_PER_LAYER_LABEL_NAME: str = "Turns Per Layer"
    # todo: add proper newlines in tooltips everywhere
    OUTER_DIAM_TOOLTIP: str = (
        "Maximum targeted outer diameter of the generated coil. "
        "Actual coil will be slighly smaller and elliptic to some extent"
    )
    ROTATION_DIRECTION_TOOLTIP: str = (
        "Rotation direction of coil, as seen on highest layer, "
        "viewed from the coil connectors, following the coil trace inwards"
    )
    TURNS_PER_LAYER_TOOLTIP: str = (
        "Minimum number of full turns (sprial) the coil trace spans, per PCB layer. "
        "There may be up to a fraction of a turn more per layer, "
        "which may sum up to multiple more coil trace spirals in the finished coil"
    )

    # todo: add coil layer selection
    def __init__(self, parent: Window):
        super().__init__(
            parent,
            [
                ConfigUnitRow(self.OUTER_DIAM_LABEL_NAME, FloatInput(
                    tooltip=self.OUTER_DIAM_TOOLTIP), self.OUTER_DIAM_UNIT_NAME),
                ConfigUnitRow(self.ROTATION_DIRECTION_LABEL_NAME,
                          RotationDirectionInput(tooltip=self.ROTATION_DIRECTION_TOOLTIP), None),
                ConfigUnitRow(self.TURNS_PER_LAYER_LABEL_NAME, IntInput(
                    tooltip=self.TURNS_PER_LAYER_TOOLTIP), None)
            ],
            self.SECTION_TITLE
        )
