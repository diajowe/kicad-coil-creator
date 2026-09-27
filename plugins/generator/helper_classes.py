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

from dataclasses import dataclass
from enum import Enum
from math import atan2, cos, degrees, radians, sin, sqrt
from typing import Self
from uuid import uuid4

from .exceptions import CoilGenException
from .legacy_kicad_interface import KicadLegacyInterface

# todo: go through anything that raises and make sure that everyhting that uses a function that raises has proper annotation

class Orientation2D(Enum):
    """
    Defines orientation of objects in 2D spaces
    """

    HORIZONTAL = 0
    VERTICAL = 1

class PointException(CoilGenException):
    """
    Custom exception grouping anything together that is related to points
    (see this library's Point class)
    """

class NormalizeException(PointException):
    """
    Custom exception raised when a Point's (see this library's Point class) radius 
    can not be normalized due to the point sitting on the origin coordinate.
    A normalization would can not be performed as the direction 
    the point should be moved to would be unclear.
    """

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
            raise NormalizeException()
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

class SpiralPosition(Enum):
    """
    Defines which side of the layer spirals an object sits on
    """

    INSIDE = 0
    OUTSIDE = 1

class PointsNotCurvingException(CoilGenException):
    """
    Custom exception raised when given points should describe a curve, but they do not
    """
    def __init__(self, start: Point, center: Point, end: Point):
        """
        Generates the exception
        :param start: Starting point of the curve that was provided
        :param center: Center point of the curve that was provided
        :param end: End point of the curve that was provided
        """
        self.start = start
        self.center = center
        self.end = end

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
            raise PointsNotCurvingException(a, b, c)

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
