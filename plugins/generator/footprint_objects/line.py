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

This file is intended to provide the footprint line structure and its configuration.
See https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html
"""

from math import sin, radians, cos
from typing import Self

from .trace import Stroke, TraceConfig

from ..exceptions import InvalidLengthException
from ..helper_classes import Layer, Orientation2D, Point, RotationDirection, Uuid
from ..legacy_kicad_interface import KicadLegacyInterface

class Line(KicadLegacyInterface):
    """
    KiCAD footprint straight line object
    """

    def __init__(self, p1: Point, p2: Point, trace_config: TraceConfig, layer: Layer):
        """
        Generate a line from two points
        :param p1: Endpoint of line
        :param p2: Endpoint of line
        :param trace_config: Parameters of a trace
        :param layer: PCB layer to place line on
        """
        self.p1 = p1
        self.p2 = p2
        self.line_width_mm = trace_config.trace_width_mm
        self.layer = layer

    @classmethod
    def from_center_and_length(
            cls,
            center: Point,
            length: float,
            orientation: Orientation2D,
            line_width_mm: float,
            layer: Layer
        ) -> Self:
        """
        Generate a line from a center point, a lengh and an orientation
        :param center: Point to center line on
        :param length: Length of line >= 0
        :param orientation: Axis to place line on
        :param line_width_mm: Width of the footprint line in mm
        :param layer: PCB layer to place line on
        :raises InvalidLengthException: If length parameter is not > 0
        """
        if length <= 0:
            raise InvalidLengthException(length)

        p1 = center.move(orientation, -(length/2))
        p2 = center.move(orientation, (length/2))

        return Line(p1, p2, line_width_mm, layer)

    def rotate(self, angle_deg: float, rotation_direction: RotationDirection):
        """
        Rotate a line around its center point
        :param angle_deg: Angle in ° to rotate line
        :param rotation_direction: Direction to rotate line around its center point
        """
        # Calculate center point of line
        center: Point = Point((self.p1.x + self.p2.x) / 2,
                              (self.p1.y + self.p2.y) / 2)

        if rotation_direction != RotationDirection.COUNTER_CLOCKWISE:
            angle_deg = 360 - angle_deg

        # normalize the points to move line center point to grid origin
        p1_normalized: Point = self.p1 - center
        p2_normalized: Point = self.p2 - center

        s: float = sin(radians(angle_deg))
        c: float = cos(radians(angle_deg))

        # rotate p1
        p1_rot_norm: Point = Point(
            p1_normalized.x * c - p1_normalized.y * s, p1_normalized.x * s + p1_normalized.y * c)

        # rotate p2
        p2_rot_norm: Point = Point(
            p2_normalized.x * c - p2_normalized.y * s, p2_normalized.x * s + p2_normalized.y * c)

        self.p1 = p1_rot_norm + center
        self.p2 = p2_rot_norm + center

    def to_legacy_api_string(self) -> str:
        return f"""
        (fp_line
		    (start {self.p1.to_legacy_api_string()})
		    (end {self.p2.to_legacy_api_string()})
		    (stroke {Stroke(self.line_width_mm).to_legacy_api_string()})
		    (layer "{self.layer.to_legacy_api_string()}")
    		(uuid {Uuid().to_legacy_api_string()})
    	)
        """
