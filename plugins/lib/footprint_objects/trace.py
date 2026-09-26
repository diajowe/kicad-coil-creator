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

This file is intended to provide the footprint trace structure and its configuration.
See https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html
"""

from enum import Enum

from ..exceptions import InvalidLengthException
from ..legacy_kicad_interface import KicadLegacyInterface

class StrokeType(Enum):
    """
    Defines stroke types, aka ways to draw a line
    """

    DASH = "dash"
    DASH_DOT = "dash_dot"
    DASH_DOT_DOT = "dash_dot_dot"
    DOT = "dot"
    DEFAULT = "default"
    SOLID = "solid"

class Stroke(KicadLegacyInterface):
    """
    Some footprint objects need to define the stroke parameters of a line being drawn.
    This class encapsulates all required stroke parameters
    """

    def __init__(self, width_mm: float, stroke_type: StrokeType = StrokeType.DEFAULT):
        """
        Defines line stroke parameters
        :param width_mm: Stroke width
        :param stroke_type: Type of line being drawn
        :raises InvalidLengthException: If width_mm is not > 0
        """
        if width_mm <= 0:
            raise InvalidLengthException(width_mm)

        self.width_mm = width_mm
        self.stroke_type = stroke_type

    def to_legacy_api_string(self) -> str:
        return f"(width {self.width_mm:.3f}) (type {self.stroke_type.value})"



class TraceConfig:
    """
    Groups together configuration parameters for traces
    """

    def __init__(self, trace_width_mm: float, trace_spacing_mm: float):
        """
        Defines trace parameters
        :param trace_width_mm: Width in mm of the actual drawn trace
        :param trace_spacing_mm: Space in mm supposed to be in between traces of a coil spiral
        :raises InvalidLengthException: If given trace_spacing_mm or trace_width_mm is <= 0
        """
        if trace_spacing_mm <= 0:
            raise InvalidLengthException(trace_spacing_mm)
        if trace_width_mm <= 0:
            raise InvalidLengthException(trace_width_mm)

        self.trace_width_mm = trace_width_mm
        self.trace_spacing_mm = trace_spacing_mm

    def get_trace_increment(self) -> float:
        """
        Returns the desirec complete increment between center points of traces
        :returns: Center point distance between two traces
        :rtype: float
        """
        return self.trace_spacing_mm + self.trace_width_mm
