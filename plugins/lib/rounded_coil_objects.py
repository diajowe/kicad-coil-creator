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

This file is intended to store class definitions that
generate coil sub-objects consisting of footprint objects
"""

from copy import deepcopy
from math import radians, sin, sqrt
from typing import Self

from .legacy_kicad_interface import KicadLegacyInterface
from .footprint_objects import Arc, Line, SolderPad, Via
from .helper_classes import (
    CoilGenException,
    ErrorMessages,
    InvalidLengthException,
    Layer,
    NotAnArcException,
    PadConfig,
    Point,
    RotationDirection,
    SpiralPosition,
    TraceConfig,
    ViaConfig
)

# todo: move exceptions to own file

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

# todo: document, do something with these
class LayerSprialException(CoilGenException):
    pass

# todo: document, do something with these
# inner needs to be smaller than outer
class RadiusMismatchException(LayerSprialException):
    def __init__(self, inner_radius_mm: float, outer_radius_mm: float):
        self.inner_radius_mm = inner_radius_mm
        self.outer_radius_mm = outer_radius_mm

# todo: document, do something with these
class InvalidLoopCountException(LayerSprialException):
    def __init__(self, loop_count: int):
        self.loop_count = loop_count

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


class ViaRingCount:
    """
    Stores number of vias on each of the two via rings
    """

    def __init__(self, inner_ring_num: int, outer_ring_num: int):
        if inner_ring_num < 0:
            raise ValueError(ErrorMessages.NUM_VIAS_LESS_THAN_ZERO)
        if outer_ring_num < 0:
            raise ValueError(ErrorMessages.NUM_VIAS_LESS_THAN_ZERO)

        self.inner_ring_num = inner_ring_num
        self.outer_ring_num = outer_ring_num

    @classmethod
    def get_num_vias(cls, layer_count: int) -> Self:
        """
        Calculates number of vias required on each via ring
        :param layer_count: Number of layers in coil
        :return: Correlation of how many vias per ring
        :rtype: ViaRingCount
        """
        # coils with uneven layer count need one extra via
        # that allows connection of the coil endpoint as
        # that coil end point would be inside the coil and
        # we do not place solder pads inside the coil
        num_vias = layer_count - (1 - layer_count % 2)
        num_vias_inside = num_vias // 2 + 1
        num_vias_outside = num_vias_inside - 1

        return ViaRingCount(num_vias_inside, num_vias_outside)


class ViaRingRadius:
    """
    Stores radius of rings on which to place connecting vias
    """

    def __init__(self, inner_radius_mm: float, outer_radius_mm: float):
        """
        Stores radius of rings on which to place connecting vias
        :param inner_radius_mm: Radius of inner via ring
        :param outer_radius_mm: Radius of outer via ring
        """
        self.inner_radius_mm = inner_radius_mm
        self.outer_radius_mm = outer_radius_mm

    @classmethod
    def get_via_radius_from_coil_params(
        cls,
        coil_outer_radius_mm: float,
        turns_per_layer: int,
        trace_config: TraceConfig,
        connecting_via_config: ViaConfig,
    ) -> Self:
        """
        Calculates diameter at which vias need to be placed.
        Vias are placed alternating on an inner circle and an outer circle
        :param coil_outer_radius_mm: Desired outer coil radius.
        Coil generation is from outside to inside, 
        so if this is too small, coil loops may collide
        :param turns_per_layer: Minimum number of turns per layer: 
        Connecting to vias might introduce up to one more full turn
        :param trace_config: Parameters of a trace
        :param connecting_via_config: Configuration for connecting vias
        :return: Calculated rings to place connecting vias on
        :rtype: ViaRingRadius
        """

        # starting from the outer radius of the coil traces,
        # remove the space of the coil itself,
        # calculated by number of turns times trace width,
        # to get the space used by the traces themselves
        # then remove the distance covered by the spaces between the coil loop traces.
        # need to take away the via radius or else the via ring will sit on a coil loop.
        # we take away half more trace width to account for width of the innermost trace
        # and alsod create a bit of breathing space and prevent via edge to collide with loop traces
        # by removing two more nonexistant loop turns.
        # this also allows space for traces connecting loops to vias
        via_inner_ring_radius_mm = coil_outer_radius_mm \
            - turns_per_layer * trace_config.trace_width_mm \
            - turns_per_layer * trace_config.trace_spacing_mm \
            - (connecting_via_config.outer_diameter_mm / 2) \
            - (0.5 * trace_config.trace_width_mm) \
            - 2 * (trace_config.trace_spacing_mm + trace_config.trace_width_mm)

        # starting from the outer radius of the coil traces
        # we need to add the via radius or else the via ring will sit on a coil loop.
        # we add two more trace width and space beetween traces to create a bit of breathing space
        # and prevent via edge to collide with loop traces
        via_outer_ring_radius_mm = coil_outer_radius_mm \
            + (connecting_via_config.outer_diameter_mm / 2) \
            + 2 * (trace_config.trace_spacing_mm + trace_config.trace_width_mm)

        return ViaRingRadius(via_inner_ring_radius_mm, via_outer_ring_radius_mm)


class ViaRings(KicadLegacyInterface):
    """
    Generates vias on two rings
    """

    def __init__(self, inner_vias: list[Via], outer_vias: list[Via]):
        """
        Stores vias in two rings
        :param inner_vias: Vias on inner ring
        :param outer_vias: Vias on outer ring
        """
        self.inner_vias = inner_vias
        self.outer_vias = outer_vias

    @classmethod
    def get_via_rings_from_settings(
        cls,
        ring_radius: ViaRingRadius,
        num_on_rings: ViaRingCount,
        config: ViaConfig
    ) -> Self:
        """
        Generates vias on two rings according to given settings
        :param ring_radius: Defines radius of the via rings
        :param nom_on_rings: Defines number of vias on each ring
        :param config: Defines the config applied to connecting vias
        :returns: Vias sorted into two rings
        :rtype: Self
        """
        inner_vias: list[Via] = []
        outer_vias: list[Via] = []

        # calculate degree steps aka how much degree between vias
        if num_on_rings.inner_ring_num != 0:
            inner_vias = ViaRings._generate_single_via_ring(
                ring_radius.inner_radius_mm,
                num_on_rings.inner_ring_num,
                config
            )

        if num_on_rings.outer_ring_num != 0:
            outer_vias = ViaRings._generate_single_via_ring(
                ring_radius.outer_radius_mm,
                num_on_rings.outer_ring_num,
                config
            )

        return ViaRings(inner_vias, outer_vias)

    @classmethod
    def _generate_single_via_ring(
        cls,
        radius: float,
        num_on_ring: int,
        config: ViaConfig
    ) -> list[Via]:
        """
        Generates vias for a single via ring with given parameters
        :param radius: Radius of ring to place vias on > 0
        :param num_on_ring: Number of vias to place on ring >= 0
        :param config: Config of connecting vias
        :rtype: list[Via]
        """
        if radius <= 0:
            raise ValueError(ErrorMessages.RADIUS_NOT_POSITIVE)
        if num_on_ring < 0:
            raise ValueError(ErrorMessages.NUM_VIAS_LESS_THAN_ZERO)

        vias: list[Via] = []
        degree_steps = 360.0 / (num_on_ring)

        for via_num in range(num_on_ring):
            # generate rotational position of via
            current_via_rotation_deg = via_num * degree_steps

            # from rotation, calculate width and height of via
            via_pos_y = sin(radians(
                current_via_rotation_deg)) * radius
            via_pos_x = sqrt(radius**2 - via_pos_y**2)
            if current_via_rotation_deg > 90 and current_via_rotation_deg < 270:
                via_pos_x *= -1

            vias.append(Via(Point(via_pos_x, via_pos_y), deepcopy(config)))

        return vias

    def to_legacy_api_string(self) -> str:
        out = ""

        all_vias: list[Via] = []
        all_vias.extend(self.inner_vias)
        all_vias.extend(self.outer_vias)

        for via in all_vias:
            out += f"{via.to_legacy_api_string()}\n"

        return out




class OutsideTraceConnector(KicadLegacyInterface):
    """
    Footprint connector used to connect other PCB parts.
    Do not mistake for connectors between vias and coil spirals (TraceInterConnector)
    """

    def __init__(
        self,
        is_upper_connector: bool,
        via_radius: ViaRingRadius,
        layer: Layer,
        connecting_via_config: ViaConfig,
        pad_config: PadConfig,
        rotation_direction: RotationDirection
    ):
        """
        Generates a connector to connect outside traces to this coil footprint
        Generates a SMD pad if connector resides on an outside layer, else a via with pad number 
        :param is_upper_connector: True if the position for the upper connector should be generated
        :param via_radius: Radius of via rings
        :param layer: Defines the layer the connector should reside on (via output is on all layers)
        :param connecting_via_config: Config for connecting vias
        :param pad_config: Config for connecting pads
        :param rotation_direction: Rotation direction of coil, from outside to inside
        """
        self.is_pad = layer.is_outside_layer
        self.center_position = OutsideTraceConnector._generate_position(
            is_upper_connector,
            via_radius,
            connecting_via_config,
            pad_config,
            rotation_direction
        )

        # on older KiCAD versions, we could generated a SMD solder pad on any layer, and it would
        # just produce as a normal trace then. Newer KiCAD version seem to not generate the SMD pad
        # when it is "buried", but also dont issue a warning. To circumvent that, we simply generate
        # a via to connect with instead of a solder pad, if the connector is not on an outside layer
        if self.is_pad:
            self.connector = SolderPad(self.center_position, pad_config, layer)
        else:
            self.connector = Via(self.center_position, connecting_via_config)

    def get_connector_position(self) -> Point:
        """
        Returns the desired position to connect with generated pad
        :returns: Position to connect with pad
        :rtype: Point
        """
        if self.is_pad:
            # todo: this should be shifted  to the edge of the pad
            return self.center_position
        else:
            return self.center_position

    @classmethod
    def _generate_position(
        cls,
        is_upper_connector: bool,
        via_radius: ViaRingRadius,
        connecting_via_config: ViaConfig,
        pad_config: PadConfig,
        rotation_direction: RotationDirection
    ) -> Point:
        """
        Calculates the target position of a connector to outside traces
        :param is_upper_connector: True if the position for the upper connector should be generated
        :param via_radius: Radius of via rings
        :param connecting_via_config: Config for connecting vias
        :param rotation_direction: Rotation direction of coil, from outside to inside
        """

        # outside trace connectors need to be placed outside
        # of the way of the outer connecting vias in x direction
        # in y direction, they need to be placed above and
        # below a possible generated connecting via with y=0
        # so that the horizontal connecting traces to the coil do not collide with the via
        x_offset = via_radius.outer_radius_mm \
            + connecting_via_config.outer_diameter_mm / 2.0 \
            + pad_config.pad_width_mm
        y_offset = connecting_via_config.outer_diameter_mm + pad_config.pad_height_mm

        center_point = Point(x_offset, y_offset)

        # if rotation direction of coil is counter clockwise,
        # pad point needs to be below x axis, else above
        if (is_upper_connector and rotation_direction == RotationDirection.CLOCKWISE) or \
                (not is_upper_connector
                 and rotation_direction == RotationDirection.COUNTER_CLOCKWISE):
            center_point.y *= -1

        return center_point

    def to_legacy_api_string(self) -> str:
        return f"""
            {self.connector.to_legacy_api_string()}
        """


class TraceInterConnector(KicadLegacyInterface):
    """
    Connector used to connect different parts of the coil
    Do not mistake for connectors to other PCB parts (OutsideTraceConnector)
    This may connect a coil layer spiral to a OutsideTraceConnector
    """

    def __init__(
        self,
        lines: list[Line],
        arcs: list[Arc],
    ):
        """
        Generates a connector to connect different parts of the coil
        :param lines: Array of Lines used to build the connector
        :param arcs: Array of Arcs used to build the connector
        """
        self.lines = lines
        self.arcs = arcs

    @classmethod
    def get_connector_for_spiral_to_outside_trace_connector(
        cls,
        trace_end: Point,
        outside_trace_connector: OutsideTraceConnector,
        trace_config: TraceConfig,
        layer_rotation_direction: RotationDirection,
        layer: Layer
    ) -> Self:
        """
        Generates connector traces between points trace end and OutsideTraceConnector,
        it will attempt to generate a seamless connection from trace_end,
        but bridge the gap to OutsideTraceConnector with a horizontal line
        :param trace_end: endpoint of trace to connect
        :param outisde_trace_connector: center point of OutsideTraceConnector to connect to
        :param trace_config: Parameters of traces
        :param layer_rotation_direction: Rotation direction of the coil layer,
        as seen from outside to inside
        :param layer: Layer to draw objects on
        """
        lines: list[Line] = []
        arcs: list[Arc] = []

        # get the straight line extending from via
        (via_line, edge_point) = TraceInterConnector._generate_line_from_via_horizontal(
            trace_end,
            outside_trace_connector,
            trace_config,
            layer
        )

        lines.append(via_line)

        # if the edge point (straight line from via outwards) and trace end point
        # are at the same position, no arc needs to be generated
        if edge_point != trace_end:
            (arcs_tmp, lines_tmp) = TraceInterConnector._generate_connecting_arcs(
                trace_end,
                edge_point,
                trace_config,
                layer_rotation_direction,
                SpiralPosition.OUTSIDE,
                layer
            )
            arcs.extend(arcs_tmp)
            lines.extend(lines_tmp)

        return TraceInterConnector(lines, arcs)

    @classmethod
    def get_connector_for_spiral_to_spiral_via(
        cls,
        trace_end: Point,
        via: Point,
        trace_config: TraceConfig,
        layer_rotation_direction: RotationDirection,
        spiral_position: SpiralPosition,
        layer: Layer
    ) -> Self:
        """
        Generates connector traces between points trace_end and via,
        for connecting layer spirals with vias that interconnect to other layer spirals 
        where trace_end is the starting point, and via is the target.
        it will attempt to generate a seamless connection from trace_end,
        but bridge the gap to via with a straight line, where the end points of this
        line reside on the same degree of the base circle
        :param trace_end: endpoint of trace to connect
        :param via: center point of via to connect to
        :param trace_config: Parameters of traces
        :param layer_rotation_direction: Rotation direction of the coil layer,
        as seen from outside to inside
        :param layer: Layer to draw objects on
        """
        lines: list[Line] = []
        arcs: list[Arc] = []

        # get the straight line extending from via
        (via_line, edge_point) = TraceInterConnector._generate_line_from_via_on_same_degree(
            trace_end,
            via,
            trace_config,
            layer_rotation_direction,
            spiral_position,
            layer
        )

        lines.append(via_line)

        # if the edge point (straight line from via outwards) and trace end point
        # are at the same position, no arc needs to be generated
        if edge_point != trace_end:
            (arcs_tmp, lines_tmp) = TraceInterConnector._generate_connecting_arcs(
                trace_end,
                edge_point,
                trace_config,
                layer_rotation_direction,
                spiral_position,
                layer
            )
            arcs.extend(arcs_tmp)
            lines.extend(lines_tmp)

        return TraceInterConnector(lines, arcs)

    @classmethod
    def _get_connector_rotation_direction(
        cls,
        layer_rotation_direction: RotationDirection,
        spiral_position: SpiralPosition
    ) -> RotationDirection:
        """
        Returns the rotation direction of this connector,
        as it is not necessarily equal to the spiral rotation direction,
        depending on which side of the coil the connector resides on
        :layer_rotation_direction: Direction the coil spiral winds on this layer,
        as seen from outside point to inside point
        :param spiral_position: Defines if the connector resides 
        on inside or outside of coil layer spiral
        :returns: Rotation direction of this connector
        :rtype: RotationDirection
        """
        # if the to be connector is residing on the outside,
        # the rotation direction as seen from trace_end to via
        # is opposite of the layer spiral rotation direction
        # else it is the same as layer spiral rotation direction
        if spiral_position == SpiralPosition.OUTSIDE:
            return layer_rotation_direction.change_rotation_direction()
        else:
            return layer_rotation_direction

    @classmethod
    def _get_degree_between_points(
        cls,
        start_point: Point,
        end_point: Point,
        layer_rotation_direction: RotationDirection,
        spiral_position: SpiralPosition
    ) -> float:
        """
        Generates the distance in degree (in proper rotation direction) from start to end
        :param start_point: Point to start travelling from
        :param end_point: Point to finish travelling to
        :layer_rotation_direction: Direction the coil spiral winds on this layer,
        as seen from outside point to inside point
        :param spiral_position: Defines if the connector resides 
        on inside or outside of coil layer spiral
        :returns: Distance in degree from start to end in rotation direction
        :rtype: float
        """
        # get individual degrees of points, in clockwise rotation direction
        # (as y increases downwards and x increases to the right)
        degree_start_point = start_point.get_angle_degree_around_origin()
        degree_end_point = end_point.get_angle_degree_around_origin()

        # get rotation direction of this connector
        connector_rotation_direction = TraceInterConnector._get_connector_rotation_direction(
            layer_rotation_direction,
            spiral_position
        )

        # calculate the actual degree difference between the points,
        # in rotation direction of the to-be connector
        if connector_rotation_direction == RotationDirection.CLOCKWISE:
            delta_degree = degree_end_point - degree_start_point
        else:
            delta_degree = (
                360.0 - (degree_end_point - degree_start_point)) % 360

        return delta_degree

    @classmethod
    def _get_absolute_spiral_radius_increase_to_target(
        cls,
        start_point: Point,
        end_point: Point,
        trace_config: TraceConfig,
        layer_rotation_direction: RotationDirection,
        spiral_position: SpiralPosition
    ) -> float:
        """
        Generates the radius difference from layer spiral end point towards via,
        as the radius difference is dependant on the degree travelled.
        Returns absolute value, even if radius would get smaller
        :param start_point: Starting point of connector line
        :param end_point: Ending point of connector line
        :param trace_config: Parameters for drawing traces
        :layer_rotation_direction: Direction the coil spiral winds on this layer,
        as seen from outside point to inside point
        :param spiral_position: Defines if the connector resides 
        on inside or outside of coil layer spiral
        :param layer: Layer to draw objects on
        :returns: Absolute value of radius delta between trace end and via position
        :rtype: float        
        """
        delta_degree = TraceInterConnector._get_degree_between_points(
            start_point,
            end_point,
            layer_rotation_direction,
            spiral_position
        )

        # calculate radius increase dependant on degree travelled
        # if a full circle is travelled, the radius should change by a full trace_increment
        # otherwise proportionate to the degrees travelled
        trace_increment = trace_config.get_trace_increment()
        return (delta_degree / 360.0) * trace_increment

    @classmethod
    def _generate_line_from_via_horizontal(
        cls,
        trace_end: Point,
        outside_trace_connector: OutsideTraceConnector,
        trace_config: TraceConfig,
        layer: Layer
    ) -> (Line, Point):
        """
        Generates the horizontal straight line from a 
        outside trace connector towards the coil spiral
        Should be used for generating connectors to OutsideTraceConnector only
        :param trace_end: Endpoint of layer spiral to connect to
        :param outside_trace_connector: OutsideTraceConector to connect to
        :param trace_config: Parameters for drawing traces
        :param layer: Layer to draw objects on
        :returns: Generated line, and endpoint to connect with further
        :rtype: (Line, Point)
        """
        connector_position = outside_trace_connector.get_connector_position()
        # find the intersection point between the extended coil spiral
        # and a horizontal line over the connector position
        # from the common circle formula (x - h)^2 + (y - k)^2 = r^2
        # solved for x = sqrt(r^2 - y^2)
        # we just assume the connector is on a circle around origin, which is accurate enough
        # as the angle towards the connector should not be that huge,
        # and the loop increment should not be noticable much.
        # generally this should not cause collision with coil spiral,
        # this function should only be used for outside trace connectors
        # and spiral gets smaller in turn direction so the spiral will not grow towards this circle
        x = sqrt(trace_end.get_radius() ** 2 - trace_end.y ** 2)

        # todo: check if x or minus x is closer
        edge_point = Point(x, connector_position.y)

        return (Line(connector_position, edge_point, trace_config, layer), edge_point)

    @classmethod
    def _generate_line_from_via_on_same_degree(
        cls,
        trace_end: Point,
        via: Point,
        trace_config: TraceConfig,
        layer_rotation_direction: RotationDirection,
        spiral_position: SpiralPosition,
        layer: Layer
    ) -> (Line, Point):
        """
        Generates the straight line from a via towards the coil spiral
        so that both end points of the line reside on the same degree.
        Should be used for generating connectors from via to layer spiral or vice versa
        :param trace_end: Endpoint of layer spiral to connect to
        :param via: Via to connect to
        :param trace_config: Parameters for drawing traces
        :layer_rotation_direction: Direction the coil spiral winds on this layer,
        as seen from outside point to inside point
        :param spiral_position: Defines if the connector resides 
        on inside or outside of coil layer spiral
        :param layer: Layer to draw objects on
        :returns: Generated line, and endpoint to connect with further
        :rtype: (Line, Point)
        """
        radius_increase_to_target = TraceInterConnector. \
            _get_absolute_spiral_radius_increase_to_target(
                trace_end,
                via,
                trace_config,
                layer_rotation_direction,
                spiral_position
            )

        # calculate the position of the point where
        # a loop extension transitions to a straight line to via
        # the edge point is adapted from the end of the coil loop
        # with the increment dependant on how many degrees travelled
        # if the connector is on the outside of a spiral, the radius needs to increase
        # else the radius needs to decrease to get closer to the via
        if spiral_position == SpiralPosition.OUTSIDE:
            edge_point = via.copy_to_radius(
                trace_end.get_radius() + radius_increase_to_target
            )
        else:
            edge_point = via.copy_to_radius(
                trace_end.get_radius() - radius_increase_to_target
            )

        return (Line(via, edge_point, trace_config, layer), edge_point)

    @classmethod
    def _generate_next_subconnector_step(
        cls,
        start_point: Point,
        end_point: Point,
        trace_config: TraceConfig,
        layer_rotation_direction: RotationDirection,
        spiral_position: SpiralPosition,
        layer: Layer,
        output_lines: list[Line],
        output_arcs: list[Arc]
    ):
        """
        Generates one of the required arcs to reach from layer spiral to via edge connector,
        or a line, in some special cases, and stores them in the output_* parameters.
        This function does not return Union[Arc|Line] as then calling code would have to 
        manually check the output type and handle unexpected types, so instead this function
        simply appends to the output_* parameters and hides type checking in its own body
        (for example if points are too close to each other and arc would collapse to a line)
        :param start_point: Starting point of connector line
        :param end_point: Ending point of connector line
        :param trace_config: Parameters for drawing traces
        :layer_rotation_direction: Direction the coil spiral winds on this layer,
        as seen from outside point to inside point
        :param spiral_position: Defines if the connector resides 
        on inside or outside of coil layer spiral
        :param layer: Layer to draw objects on
        :param output_lines: Array of lines to append to
        :param output_arcs: Array of arcs to append to
        """
        # get individual degrees of points, in clockwise rotation direction
        # (as y increases downwards and x increases to the right)
        degree_start_point = start_point.get_angle_degree_around_origin()
        degree_end_point = end_point.get_angle_degree_around_origin()

        # get rotation direction of this connector
        connector_rotation_direction = TraceInterConnector._get_connector_rotation_direction(
            layer_rotation_direction,
            spiral_position
        )

        radius_increase_to_target = TraceInterConnector. \
            _get_absolute_spiral_radius_increase_to_target(
                start_point,
                end_point,
                trace_config,
                layer_rotation_direction,
                spiral_position
            )

        # generate the center point radius of the connecting arc that is generated
        # the arc radius is exactly in the middle between start and end point radius radius
        if spiral_position == SpiralPosition.OUTSIDE:
            arc_middle_radius = start_point.get_radius() + (radius_increase_to_target / 2.0)
        else:
            arc_middle_radius = start_point.get_radius() - (radius_increase_to_target / 2.0)

        # this arc will be drawn from start to end,
        # so start needs to have a smaller angle as end
        # for the following center angle calculation to work
        if degree_start_point > degree_end_point:
            degree_end_point -= 360

        center_angle = (degree_start_point + degree_end_point) / 2.0

        if connector_rotation_direction == RotationDirection.COUNTER_CLOCKWISE:
            center_angle = center_angle - 180

        # generate arc extending the coil spiral
        # this may fail because the rotation direction cannot be determined
        # due to all points forming a straight line
        # we will simply generate a line
        try:
            output_arcs.append(
                Arc(
                    start_point,
                    Point.get_point_on_circle(
                        arc_middle_radius, center_angle),
                    end_point,
                    trace_config,
                    layer
                ))
        except NotAnArcException:
            output_lines.append(
                Line(start_point, end_point, trace_config, layer))

    @classmethod
    def _generate_connecting_arcs(
        cls,
        trace_end: Point,
        edge_point: Point,
        trace_config: TraceConfig,
        layer_rotation_direction: RotationDirection,
        spiral_position: SpiralPosition,
        layer: Layer
    ) -> (list[Arc], list[Line]):
        """
        Generates all lines and arcs to connect the trace end to a via edge connector
        :param trace_end: End of spiral trace to connect to
        :param edge_point: Edge connector of via,
        extending via towards the spiral on the same radius
        :param trace_config: Parameters for drawing traces
        :layer_rotation_direction: Direction the coil spiral winds on this layer,
        as seen from outside point to inside point
        :param spiral_position: Defines if the connector resides 
        on inside or outside of coil layer spiral
        :param layer: Layer to draw objects on
        """
        arcs: list[Arc] = []
        lines: list[Line] = []

        delta_degree = TraceInterConnector._get_degree_between_points(
            trace_end,
            edge_point,
            layer_rotation_direction,
            spiral_position
        )

        if delta_degree > 180:
            # for connections longer than 180 degrees, the path needs to split into two arcs
            # because arcs cannot generate a spiral loop but reside on a full circle.
            # because of that the loop is generally split into two
            # the split point will be fixed at 180° with half the increment required for a full loop
            if spiral_position == SpiralPosition.OUTSIDE:
                intermediate_radius = trace_end.get_radius() \
                    + (trace_config.get_trace_increment() / 2.0)
            else:
                intermediate_radius = trace_end.get_radius() \
                    - (trace_config.get_trace_increment() / 2.0)

            intermediate_point = Point.get_point_on_circle(
                intermediate_radius, 180.0)

            TraceInterConnector._generate_next_subconnector_step(
                trace_end,
                intermediate_point,
                trace_config,
                layer_rotation_direction,
                spiral_position,
                layer,
                lines,
                arcs
            )

            TraceInterConnector._generate_next_subconnector_step(
                intermediate_point,
                edge_point,
                trace_config,
                layer_rotation_direction,
                spiral_position,
                layer,
                lines,
                arcs
            )
        else:
            # only one part needed, directly connect trace and edge point
            TraceInterConnector._generate_next_subconnector_step(
                trace_end,
                edge_point,
                trace_config,
                layer_rotation_direction,
                spiral_position,
                layer,
                lines,
                arcs
            )

        return (arcs, lines)

    def to_legacy_api_string(self) -> str:
        out = ""
        for line in self.lines:
            out += line.to_legacy_api_string()
        for arc in self.arcs:
            out += arc.to_legacy_api_string()
        return out

