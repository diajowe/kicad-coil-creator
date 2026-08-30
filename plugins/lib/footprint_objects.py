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

This file is intended to store class definitions that directly translate to KiCAD footprints.
See https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html
for objects of which some are implemented here
"""

from typing import Self

from math import radians, sin, cos

from .helper_classes import (
    InvalidLengthException,
    Layer,
    Orientation2D,
    PadConfig,
    PadShape,
    PadType,
    Point,
    RotationDirection,
    Stroke,
    TraceConfig,
    Uuid,
    ViaConfig
)
from .legacy_kicad_interface import KicadLegacyInterface

# todo: use config objects for all of those, like ViaConfig, and USE THEM EVERYWHERE

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

class Via(KicadLegacyInterface):
    """
    KiCAD footprint via object
    """

    def __init__(self, position: Point, config: ViaConfig):
        """
        Generate a via at a position
        :param position: Center position of the via
        :param config: Configuration parameters of via
        """
        self.position = position
        self.config = config

    def get_center_point(self) -> Point:
        """
        Returns the center point of this via
        :returns: Center point of the via
        :rtype: Point
        """
        return self.position

    def to_legacy_api_string(self) -> str:
        return f"""
        (pad "{self.config.pad_num}" {PadType.THRU_HOLE.value} {PadShape.CIRCLE.value}
    		(at {self.position.to_legacy_api_string()})
    		(size {self.config.outer_diameter_mm} {self.config.outer_diameter_mm})
    		(drill {self.config.drill_diameter_mm})
    		(layers *.Cu)
    		(remove_unused_layers yes)
    		(keep_end_layers yes)
    		(uuid {Uuid().to_legacy_api_string()})
    	)
        """

class SolderPad(KicadLegacyInterface):
    """
    KiCAD footprint solder pad object
    """

    def __init__(
        self,
        position: Point,
        pad_config: PadConfig,
        layer: Layer
        ):
        """
        Generate a solder pad at a position
        :param position: Center position of the solder pad
        :param pad_config: Configuration parameters of the pad
        :param layer: PCB layer to place line on
        """

        self.position = position
        self.config = pad_config
        self.layer = layer

    def to_legacy_api_string(self) -> str:
        return f"""
        (pad "{self.config.pad_num}" {PadType.SMD.value} {PadShape.ROUNDRECT.value}
        	(at {self.position.to_legacy_api_string()})
        	(size {self.config.pad_width_mm:.3f} {self.config.pad_height_mm:.3f})
        	(layers "{self.layer.to_legacy_api_string()}")
        	(roundrect_rratio 0.25)
        	(uuid {Uuid().to_legacy_api_string()})
        )
        """

class FootprintProperty(KicadLegacyInterface):
    """
    KiCAD footprint property tag object, consisting of a key value pair
    """

    def __init__(
        self,
        position: Point,
        layer: Layer,
        key: str,
        value: str
        ):
        """
        Generate a footprint property object at a position, on a layer
        :param position: Center position of the object to place
        :param layer: Layer to place property object on
        :param key: Key to use for the property object
        :param value: Value to use for the property object
        """
        self.position = position
        self.layer = layer
        self.key = key
        self.value = value

    def to_legacy_api_string(self) -> str:
        return f"""
	    (property "{self.key}" "{self.value}"
	    	(at {self.position.to_legacy_api_string()})
	    	(unlocked yes)
	    	(layer "{self.layer.to_legacy_api_string()}")
	    	(hide no)
	    	(effects
	    		(font
	    			(size 1 1)
	    			(thickness 0.15)
	    		)
	    	)
	    )
        """
