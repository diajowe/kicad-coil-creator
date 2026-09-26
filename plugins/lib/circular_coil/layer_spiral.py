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

This file is intended to provide the structure to generate
tracess of an entire coil spiral on one layer
"""

from typing import Self

from ..exceptions import CoilGenException, InvalidLengthException
from ..footprint_objects.arc import Arc
from ..footprint_objects.trace import TraceConfig
from ..helper_classes import Layer, Point, RotationDirection, SpiralPosition
from ..legacy_kicad_interface import KicadLegacyInterface

class LayerSpiralException(CoilGenException):
    """
    Custom exception grouping anything together that is related to layer spirals
    on circular coils
    (see this library's LayerSpiral class)
    """

class RadiusMismatchException(LayerSpiralException):
    """
    Custom exception raised when a spirals desired inner radius is >= desired outer radius  
    """
    def __init__(self, inner_radius_mm: float, outer_radius_mm: float):
        """
        Generates the exception
        :param inner_radius_mm: Given inner radius incompatible with outer radius
        :param outer_radius_mm: Given outer radius incompatible with inner radius
        """
        self.inner_radius_mm = inner_radius_mm
        self.outer_radius_mm = outer_radius_mm

class InvalidLoopCountException(LayerSpiralException):
    """
    Custom exception raised when a spirals desired loop count is <= 0  
    """
    def __init__(self, loop_count: int):
        """
        Generates the exception
        :param loop count: Given invalid number of loops to draw
        """
        self.loop_count = loop_count

class SpiralLoop(KicadLegacyInterface):
    """
    Generates one loop of a spiral, from outside to inside
    """

    def __init__(
        self,
        arc1: Arc,
        arc2: Arc
    ):
        """
        Stores one loop of a layer spiral
        :param arc1: First half of the loop
        :param arc2: Second half of the loop
        """
        self.arc1 = arc1
        self.arc2 = arc2

    def get_start_point(self) -> Point:
        """
        Returns the start point of this coil spiral,
        where a coil spiral always generates from outside to inside
        """
        return self.arc1.get_start_point()

    def get_end_point(self) -> Point:
        """
        Returns the ending point of this coil spiral,
        where a coil spiral always generates from outside to inside
        """
        return self.arc2.get_end_point()


    @classmethod
    def get_spiral_loop_from_params(
        cls,
        outer_radius_mm: float,
        trace_config: TraceConfig,
        layer: Layer,
        rotation_direction: RotationDirection
    ) -> Self:
        """
        Generates one loop of a layer spiral, with a certain trace width.
        Rotation direction is seen from outer end point of loop
        :param outer_radius_mm: Radius of outer end point of loop, 
        if drawn on a circle concentric to origin
        :param trace_config: Parameters for traces
        :param layer: Layer to draw loop on
        :param rotation_direction: Rotation direction of spiral loop is part of
        :raises InvalidLengthException: If given outer_radius_mm is <= 0
        """
        if outer_radius_mm <= 0:
            raise InvalidLengthException(outer_radius_mm)
        # horizontal offset from spiral start point to end point
        trace_increment = trace_config.trace_spacing_mm + trace_config.trace_width_mm

        # arc outer points
        p1 = Point(outer_radius_mm, 0)
        p2 = Point(-outer_radius_mm + trace_config.get_trace_increment() / 2.0, 0)
        p3 = Point(outer_radius_mm - trace_increment, 0)

        # arc center points
        p1_2 = Point(0, outer_radius_mm - trace_config.get_trace_increment() / 4.0)
        p2_3 = Point(trace_increment / 2.0, -(outer_radius_mm - (trace_increment * 0.75)))

        # depending on rotation direction, center points of arc need to be on other side of x axis
        if rotation_direction != RotationDirection.CLOCKWISE:
            p1_2.y *= -1
            p2_3.y *= -1

        return SpiralLoop(
            Arc(p1, p1_2, p2, trace_config, layer),
            Arc(p2, p2_3, p3, trace_config, layer)
        )

    def to_legacy_api_string(self) -> str:
        return f"""
        {self.arc1.to_legacy_api_string()}
        {self.arc2.to_legacy_api_string()}
        """

class LayerSpiral(KicadLegacyInterface):
    """
    Generates the entire spiral for an entire coil layer
    """

    def __init__(self, loops: list[SpiralLoop], inner_radius_mm: float , outer_radius_mm: float):
        """
        Generates the single spiral for an entire coil layer
        :param loops: All loops generated for a coil
        :param inner_radius_mm: Smaller radius of the coil layer spiral in mm
        :param outer_radius_mm: Greater radius of the coil layer spiral in mm
        """
        if outer_radius_mm <= inner_radius_mm:
            raise RadiusMismatchException(inner_radius_mm, outer_radius_mm)

        self.loops = loops
        self.outer_radius_mm = outer_radius_mm
        self.inner_radius_mm = inner_radius_mm


    @classmethod
    def get_layer_spiral(
        cls,
        loop_count: int,
        outer_radius_mm: float,
        trace_config: TraceConfig,
        layer: Layer,
        rotation_direction: RotationDirection
    ) -> Self:
        """
        Generates the entire spiral for an entire coil layer
        :param loop_count: How many loops the spiral should have
        :param outer_radius_mm: Outer radius of coil spiral
        :param trace_config: Parameters for traces
        :param layer: Layer to draw loop on
        :param rotation_direction: Rotation direction of spiral loop is part of
        :returns: Full coil spiral, without connectors
        :rtype: LayerSpiral
        """
        if outer_radius_mm <= 0:
            raise InvalidLengthException(outer_radius_mm)
        if loop_count <= 0:
            raise InvalidLoopCountException(loop_count)

        loops: list[SpiralLoop] = []

        next_outer_radius_mm = outer_radius_mm

        # generate required number of loops
        for _ in range(loop_count):
            current_loop = SpiralLoop.get_spiral_loop_from_params(
                next_outer_radius_mm,
                trace_config,
                layer,
                rotation_direction
            )

            next_outer_radius_mm = current_loop.get_end_point().x

            loops.append(current_loop)

        return LayerSpiral(loops, next_outer_radius_mm, outer_radius_mm)

    def get_end_point(self, position: SpiralPosition) -> Point:
        """
        Returns the endpoint position of the layer spiral
        :param position: Defines if the inner our outer connection point is desired
        :returns: Position enf the spiral endpoint
        :rtype: Point
        """
        if position == SpiralPosition.INSIDE:
            return Point(self.inner_radius_mm, 0)
        else:
            return Point(self.outer_radius_mm, 0)

    def to_legacy_api_string(self) -> str:
        out = ""
        for l in self.loops:
            out += l.to_legacy_api_string()
        return out

