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

This file is intended to provide a ui element for footprint's FootprintConfig.
This allows the usage as WX element and helps building the coil generator's UI.
"""

# todo: document

import wx
from wx import Window

from .config_panel import ButtonInputConnector, ConfigPanel, ConfigButton, ConfigButtonRow
from .config_input import StringInput


class FootprintConfigPanel(ConfigPanel):
    SECTION_TITLE: str = "Footprint Configuration"
    NAME_LABEL_NAME: str = "Name"
    NAME_TOOLTIP: str = (
        "Coil name used to mark the generated coil in the PCB. "
        "Will also be used as identifying name when saving coil as footprint."
    )
    DEFAULT_COIL_NAME: str = "COIL_DEFAULT"
    BUTTON_TOOLTIP: str = "Generate a default footprint name"

    def __init__(self, parent: Window):
        super().__init__(
            parent,
            [
                ConfigButtonRow(
                    self.NAME_LABEL_NAME,
                    StringInput(tooltip=self.NAME_TOOLTIP),
                    ConfigButton(
                        wx.ART_REDO,
                        self.__restore_default_name,
                        tooltip=self.BUTTON_TOOLTIP
                        )
                    ),
            ],
            self.SECTION_TITLE
        )

    def __restore_default_name(self, event: wx.Event, connector: ButtonInputConnector):
        # todo: all event callbacks need to be wrapped in a function that catches and logs exceptions
        # continue processing event after this handler finishes
        event.Skip()

        # only processing button press events
        if event.GetEventType() == wx.wxEVT_BUTTON:
            # with stronger typing this does not work, as connector
            # contains a Control, which has no SetValue function,
            # but really underneath is a TextCtrl, which does!
            # this won't work any more if someone changes the Control object given here 
            connector.input.SetValue(self.DEFAULT_COIL_NAME)
