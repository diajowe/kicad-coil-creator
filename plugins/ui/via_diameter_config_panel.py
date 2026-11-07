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

This file is intended to provide a ui element for generator's ViaDiameterConfig.
This allows the usage as WX element and helps building the coil generator's UI.
"""

# todo: document

from wx import Window

from .config_panel import ConfigPanel, ConfigUnitRow
from .config_input import FloatInput


class ViaDiameterConfigPanel(ConfigPanel):
    SECTION_TITLE: str = "Via Diameter Configuration"
    VIA_OUTER_DIAMETER_LABEL_NAME: str = "Outer Diameter"
    VIA_DRILL_DIAMETER_LABEL_NAME: str = "Drill Hole Diameter"
    VIA_UNIT_NAME: str = "mm"
    VIA_OUTER_DIAMETER_TOOLTIP: str = (
        "Diameter of the generated via ring. "
        "Must be greater than drill diameter, or else the drill bit would destroy the via ring"
    )
    VIA_DRILL_DIAMETER_TOOLTIP: str = (
        "Diameter of the drill hole through the generated via. "
        "Must be smaller than outer diameter, or else the drill bit would destroy the via ring"
    )

    def __init__(self, parent: Window):
        super().__init__(
            parent,
            [
                ConfigUnitRow(self.VIA_OUTER_DIAMETER_LABEL_NAME,
                          FloatInput(tooltip=self.VIA_OUTER_DIAMETER_TOOLTIP), self.VIA_UNIT_NAME),
                ConfigUnitRow(self.VIA_DRILL_DIAMETER_LABEL_NAME, FloatInput(
                    tooltip=self.VIA_DRILL_DIAMETER_TOOLTIP), self.VIA_UNIT_NAME),
            ],
            self.SECTION_TITLE
        )
