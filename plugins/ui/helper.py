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

This file is intended to provide helper classes and functions that
did not find a place in better specified structures
"""

from typing import Callable

import logging
import traceback
import wx

def get_default_obj_spacing() -> int:
    """
    Fetches and returns the desired default spacing between UI objects in pixels
    :returns: Desired space between objects in pixel
    :rtype: int
    """
    # making object spacing dependent on font size
    # to nicely scale with different resolutions
    return wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)\
        .GetPixelSize().GetWidth()

def callback_logging_wrapper(
    callback: Callable[[wx.Event],None]
    ) -> Callable[[wx.Event],None]:
    """
    Generates a wrapper around the event callback given that will
    log an exception in the callback if one occurs.
    Otherwise an exception thrown in the callback would not be visible in
    our kicad plugin context
    :param callback: The event callback to call and wrap
    :returns: The properly log wrapped event callback function
    :rtype: Callable[[wx.Event],None]
    """
    logger = logging.getLogger()
    def callback_wrapper_inner(event: wx.Event):
        try:
            callback(event)
        except Exception as e: # pylint: disable=broad-except
            logger.error("Exception thrown in event handler:")
            logger.error(repr(e))
            logger.error(traceback.format_exc())

    return callback_wrapper_inner