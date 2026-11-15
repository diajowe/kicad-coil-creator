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

This file is intended to provide a ui element for generator's TraceConfig.
This allows the usage as WX element and helps building the coil generator's UI.
"""

# todo: document

from wx import Window

from .config_input import FloatInput
from .config_panel import ConfigPanel, ConfigUnitRow

from ..generator.footprint_objects.trace import TraceConfig

class TraceConfigPanel(ConfigPanel):
    SECTION_TITLE: str = "Trace Configuration"
    TRACE_WIDTH_LABEL_NAME: str = "Trace Width"
    TRACE_SPACING_LABEL_NAME: str = "Trace Spacing"
    TRACE_UNIT_NAME: str = "mm"
    TRACE_WIDTH_TOOLTIP: str = \
        "Width of the drawn trace that is constitutes parts of the generated coil"
    TRACE_SPACING_TOOLTIP: str = "Gap between traces of coil sprials on one layer"
    TRACE_WIDTH_ID: str = "trace_width_mm"
    TRACE_SPACING_ID: str = "trace_spacing_mm"

    def __init__(self, parent: Window):
        # if editing anything regarding the input objects,
        # also change restore_from_saved and get_current_displayed_config
        super().__init__(
            parent,
            [
                ConfigUnitRow(self.TRACE_WIDTH_ID, self.TRACE_WIDTH_LABEL_NAME,
                    FloatInput(
                        TraceConfig.get_width_range(),
                        TraceConfig.get_width_default(),
                        self.TRACE_WIDTH_TOOLTIP
                        ),
                    self.TRACE_UNIT_NAME
                    ),
                ConfigUnitRow(self.TRACE_SPACING_ID, self.TRACE_SPACING_LABEL_NAME,
                    FloatInput(
                        TraceConfig.get_spacing_range(),
                        TraceConfig.get_spacing_default(),
                        self.TRACE_SPACING_TOOLTIP
                        ),
                    self.TRACE_UNIT_NAME
                    ),
            ],
            self.SECTION_TITLE
        )
