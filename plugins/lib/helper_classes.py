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

This file is intended to store objects aiding in creating coil
footprints that do not directly translate to footprint contents
"""

from uuid import uuid4
from typing import Self, Union
from dataclasses import dataclass
from enum import Enum
from math import atan2, cos, degrees, radians, sin, sqrt

from .legacy_kicad_interface import KicadLegacyInterface

# todo: go through anything that raises and make sure that everyhting that uses a function that raises has proper annotation
# todo: go through everything and make sure everything has proper docu

# todo: document
class CoilGenException(Exception):
    pass

# todo: document, do something with these
class CoilGenTypeError(CoilGenException):
    def __init__(self, expected: str, got: str):
        self.expected = expected
        self.got = got

# todo: document, do something with these
class CoilGenValueException(CoilGenException):
    def __init__(self, value: Union[int, float]):
        self.value = value

# todo: document, do something with these
class PointNormalizeException(CoilGenException):
    pass

# todo: document, do something with these
# > 0
class InvalidLengthException(CoilGenValueException):
    pass

# todo: document, do something with these
class PadNumException(CoilGenException):
    pass

class Orientation2D(Enum):
    """
    Defines orientation of objects in 2D spaces
    """

    HORIZONTAL = 0
    VERTICAL = 1

@dataclass
class Point(KicadLegacyInterface):
    """
    Footprint objects need to be defined somehow. 
    One option to define these structures is via points
    X increases towards right screen border,
    Y increases towards bottom screen border
    """
    x: float
    y: float

    def __init__(self, x: float, y: float):
        """
        Define a point with it's x an y coordinate
        X increases towards right screen border,
        Y increases towards bottom screen border
        :param x: X Coordinate part
        :param y: Y Coordinate part
        """
        self.x = x
        self.y = y

    def __add__(self, other: Self):
        """
        Adds one point to another
        :param other: Point to add to this one
        """
        return Self(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Self):
        """
        Subtracts one point to another
        :param other: Point to subtract from this one
        """
        return Self(self.x - other.x, self.y - other.y)

    @classmethod
    def get_point_on_circle(cls, radius: float, angle_degree: float) -> Self:
        """
        Generates a point on a cicle around the origin with radius on
        the specified angle position
        If the point were sitting on a circle around the origin point
        angle 90° would be on the line through origin and x=0,y=1,
        angle 180° would be on the line through origin and x=-1,y=0
        Works with degrees outside of 0..360 range
        :param radius: Radius of the circle with origin as centerpoint
        :param angle_degree: Angle in degree on the circle to place the point on
        :returns: Point on a defined circle concentric around origin, placed at angle
        :rtype: Point
        """
        x = radius * cos(radians(angle_degree))
        y = radius * sin(radians(angle_degree))

        return Point(x,y)

    def move(self, orientation: Orientation2D, distance: float):
        """
        Moves this point on the coordinate system
        :param orientation: Axis to move point along
        :param distance: Distance to move point for
        """
        match orientation:
            case Orientation2D.HORIZONTAL:
                self.x += distance
            case Orientation2D.VERTICAL:
                self.y += distance

    def normalize_radius(self) -> Self:
        """
        Normalizes a point's radius aka radius length = 1, if circle center is origin
        :returns: Point with normalized radius
        :rtype: Point
        :raises PointNormalizeException: If the point radius cannot 
        be normalizes because the point is on origin point
        """
        length = self.get_radius()
        if length == 0.0:
            raise PointNormalizeException()
        return Point(self.x / length, self.y / length)

    def get_radius(self) -> float:
        """
        Returns the radius of this point,
        if the point were on a circle whose center point is the origin
        :returns: Radius of the circle
        :rtype: float
        """
        return sqrt(self.x * self.x + self.y * self.y)

    def copy_to_radius(self, target_radius: float) -> Self:
        """
        Generates a new point on the same angle as this point, and
        sets the new point's radius to a specific length,
        if the point were on a circle whose center point is the origin
        :param target_radius: Desired point radius
        :returns: Point with defined radius
        :rtype: Point
        """
        normalized = self.normalize_radius()
        return Point(normalized.x * target_radius, normalized.y * target_radius)

    def get_angle_degree_around_origin(self) -> float:
        """
        Returns the angle of the point,
        if the point were sitting on a circle around the origin point
        x=0,y=1 returns angle 90°, x=-1,y=0 returns angle 180°
        :returns: Angle in degrees
        :rtype: float
        """
        return degrees(atan2(float(self.y), float(self.x))) % 360.0

    def to_legacy_api_string(self) -> str:
        # Points are usually defined as just x followed by y, no brackets, nothing
        return f"{self.x:.3f} {self.y:.3f}"

# todo: document, do something with these
class NotAnArcException(CoilGenException):
    def __init__(self, start: Point, center: Point, end: Point):
        self.start = start
        self.center = center
        self.end = end

# todo: make error messages more helpful. contain wrong value, code line etc
class ErrorMessages(Enum):
    """
    Defines error messages used in coil messages
    """

    NUM_VIAS_LESS_THAN_ZERO = "Given number of vias to place is not >= 0"
    LAYER_COUNT_NOT_POSITIVE = "Given layer count is not > 0"
    TURNS_PER_LAYER_NOT_POSITIVE = "Given number of turns per layer is not > 0"
    COIL_OUTER_DIAMETER_NOT_POSITIVE = "Given coil outer diameter is not > 0"
    VIA_DIAMETER_NOT_POSITIVE = "Given via diameter is not > 0"
    VIA_DRILL_NOT_POSITIVE = "Given via drill hole diameter is not > 0"
    LOOP_INCREMENT_NOT_POSITIVE = "Given loop increment is not > 0"
    RADIUS_NOT_POSITIVE = "Given radius is not > 0"
    WIDTH_NOT_POSITIVE = "Given width is not > 0"

class SpiralPosition(Enum):
    """
    Defines which side of the layer spirals an object sits on
    """

    INSIDE = 0
    OUTSIDE = 1

class RotationDirection(Enum):
    """
    Defines rotation directions around a center point
    """

    CLOCKWISE = 0
    COUNTER_CLOCKWISE = 1

    def change_rotation_direction(self) -> Self:
        """
        Switches the rotation direction around
        """
        # match may not be available as KiCAD may ship with older python versions
        if self == RotationDirection.CLOCKWISE:
            return RotationDirection.COUNTER_CLOCKWISE
        else:
            return RotationDirection.CLOCKWISE

    @classmethod
    def get_rotation_direction(cls, a: Point, b: Point, c: Point) -> Self:
        """
        Traverses three points in order of a -> b -> c and returns the traversal direction.
        :param a: Point a, starting point
        :param b: Point b, second point traversed
        :param c: Point c, last point traversed
        :raises NotAnArcException: If all points are on a line
        """
        # in KiCAD, y increases downwards, whereas the model below assumes y assumes upwards
        # simply switching sign of y, to account for that
        ay = -a.y
        by = -b.y
        cy = -c.y

        vec_ab = (b.x - a.x, by - ay)
        vec_bc = (c.x - b.x, cy - by)
        crossproduct_2d = vec_ab[0] * vec_bc[1] - vec_ab[1] * vec_bc[0]

        if crossproduct_2d < 0:
            return RotationDirection.CLOCKWISE
        elif crossproduct_2d > 0:
            return RotationDirection.COUNTER_CLOCKWISE
        else:
            raise NotAnArcException(a, b, c)

class Uuid(KicadLegacyInterface):
    """
    Some footprint objects need an UUID designated to them.
    This generates a UUID on creation of an Uuid object
    """

    def __init__(self):
        """
        Generates a UUID as object instanciation
        """
        self.uuid = uuid4()

    def to_legacy_api_string(self) -> str:
        return f"{str(self.uuid)}"

class Layer(KicadLegacyInterface):
    """
    Footprint objects need to define which layer they are on.
    This class encapsulates layers to not use "str" inside footprint objects
    """

    def __init__(self, layer_name: str, is_outside_layer: bool):
        """
        Generates the layer_name object
        :param layer_name: String name of this layer
        :param is_outside_layer: Defines if the layer is one of the outside layers of the PCB
        """
        # todo: have more validation for this string
        # todo: have this an int and generate name from it
        self.layer_name = layer_name
        self.is_outside_layer = is_outside_layer

    def to_legacy_api_string(self) -> str:
        return f"{self.layer_name}"

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

class PadType(Enum):
    """
    Defines type of footprint pad
    """

    THRU_HOLE = "thru_hole"
    SMD = "smd"
    CONNECT = "connect"
    NP_THRU_HOLE = "np_thru_hole"

class PadShape(Enum):
    """
    Defines shape of footprint pad
    """

    CIRCLE = "circle"
    RECT = "rect"
    OVAL = "oval"
    TRAPEZOID = "trapezoid"
    ROUNDRECT = "roundrect"
    CUSTOM = "custom"

# todo: document, do something with these
class ViaException(CoilGenException):
    pass

# todo: document, do something with these
# drill needs to be smaller than outer
class DiameterMismatchException(ViaException):
    def __init__(self, outer_diameter_mm: float, drill_diameter_mm: float):
        self.outer_diameter_mm = outer_diameter_mm
        self.drill_diameter_mm = drill_diameter_mm

class ViaConfig:
    """
    Groups together configuration parameters of vias
    """

    CONNECTING_VIA_PAD_NUM: int = 0

    def __init__(self, pad_num: int, outer_diameter_mm: float, drill_diameter_mm: float):
        """
        Defines via parameters
        :param pad_num: Number of pad >= 0, should be unique for all used pads in footprint
        :param outer_diameter_mm: Diameter in mm of entire via. Has to be > drill_diameter_mm
        :param drill_diameter_mm: Diameter in mm of drill hole. Has to be < outer_diameter_mm
        :raises PadNumException: If given pad_num is < 0
        :raises InvalidLengthException: If given outer_diameter_mm or drill_diameter_mm is <= 0
        :raises DiameterMismatchException: If given outer_diameter_mm is <= drill_diameter_mm
        """
        if pad_num < 0:
            raise PadNumException(pad_num)
        if drill_diameter_mm <= 0 or outer_diameter_mm <= 0:
            raise InvalidLengthException(drill_diameter_mm)
        if outer_diameter_mm <= drill_diameter_mm:
            raise DiameterMismatchException(outer_diameter_mm, drill_diameter_mm)

        self.outer_diameter_mm = outer_diameter_mm
        self.pad_num = pad_num
        self.drill_diameter_mm = drill_diameter_mm

    @classmethod
    def get_connecting_via_config(cls, outer_diameter_mm, drill_diameter_mm: int) -> Self:
        """
        Defines via parameters for connecting vias (where pad number is static)
        :param outer_diameter_mm: Diameter in mm of entire via. Has to be > drill_diameter_mm
        :param drill_diameter_mm: Diameter in mm of drill hole. Has to be < outer_diameter_mm
        :return: Parameters for connecting vias
        :rtype: ViaConfig
        """

        return ViaConfig(ViaConfig.CONNECTING_VIA_PAD_NUM, outer_diameter_mm, drill_diameter_mm)

class PadConfig:
    """
    Groups together configuration parameters of smd pads
    """

    def __init__(self, pad_num: int, pad_width_mm: float, pad_height_mm: float):
        """
        Defines pad parameters
        :param pad_num: Number of pad >= 0, should be unique for all used pads in footprint
        :param pad_width_mm: Desired width of a possible connector pad > 0
        :param pad_height_mm: Desired height of a possible connector pad > 0
        :raises PadNumException: If given pad_num is < 0
        :raises InvalidLengthException: If given pad_width_mm or pad_heigh_mm is <= 0
        """
        if pad_num < 0:
            raise PadNumException(pad_num)
        if pad_width_mm <= 0:
            raise InvalidLengthException(pad_width_mm)
        if pad_height_mm <= 0:
            raise InvalidLengthException(pad_height_mm)

        self.pad_num = pad_num
        self.pad_width_mm = pad_width_mm
        self.pad_height_mm = pad_height_mm

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