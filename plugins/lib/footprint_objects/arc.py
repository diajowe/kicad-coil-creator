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

This file is intended to provide the footprint arc structure and its configuration.
See https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html
"""

from .trace import Stroke, TraceConfig

from ..legacy_kicad_interface import KicadLegacyInterface
from ..helper_classes import Layer, Point, RotationDirection, Uuid

class Arc(KicadLegacyInterface):
    """
    KiCAD footprint curved line object
    """

    def __init__(
        self,
        start: Point,
        center: Point,
        end: Point,
        trace_config: TraceConfig,
        layer: Layer
        ):
        """
        Generate a curved line from two points and the centerpoint
        defining the radius and orientation of curvature
        :param start: Starting point of line
        :param center: Center point of curved line, defining radius and orientation of curvature
        :param end: Ending point of line
        :param trace_config: Parameters for a trace
        :param layer: PCB layer to place arc on
        """
        # mark original start and end points as given by parameters
        # not to use for drawing but for getters
        self.orig_start = start
        self.orig_end = end

        # older KiCAD versions draw arcs always in clockwise turn direction,
        # and use the center point only to calculate curve radius.
        # to account for this, switch start and end point to always be in clockwise direction
        if RotationDirection.get_rotation_direction(start, center, end) \
            == RotationDirection.COUNTER_CLOCKWISE:
            self.start = end
            self.end = start
        else:
            self.start = start
            self.end = end

        self.center = center
        self.trace_config = trace_config
        self.layer = layer

    def get_start_point(self) -> Point:
        """
        Returns the starting point of this arc, as given via parameter.
        Not actual starting point for drawing, as due to older KiCAD versions,
        arcs have to be drawn in clockwise turning order
        """
        return self.orig_start

    def get_end_point(self) -> Point:
        """
        Returns the ending point of this arc, as given via parameter.
        Not actual ending point for drawing, as due to older KiCAD versions,
        arcs have to be drawn in clockwise turning order
        """
        return self.orig_end

    def to_legacy_api_string(self) -> str:
        return f"""
        (fp_arc
            (start {self.start.to_legacy_api_string()})
            (mid {self.center.to_legacy_api_string()})
            (end {self.end.to_legacy_api_string()})
		    (stroke {Stroke(self.trace_config.trace_width_mm).to_legacy_api_string()})
            (layer "{self.layer.to_legacy_api_string()}")
            (uuid {Uuid().to_legacy_api_string()})
	    )
        """

