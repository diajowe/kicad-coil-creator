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

This file is intended to provide the structure to connect layer spirals
(see layer_spirals.py) to vias or other structures belonging to the coil
"""

from math import sqrt
from typing import Self

from .external_geometry_connector import ExternalGeometryConnector

from ..footprint_objects.arc import Arc
from ..footprint_objects.line import Line
from ..footprint_objects.trace import TraceConfig
from ..helper_classes import (
    Layer,
    Point,
    PointsNotCurvingException,
    RotationDirection,
    SpiralPosition
)
from ..legacy_kicad_interface import KicadLegacyInterface

class TraceInterConnector(KicadLegacyInterface):
    """
    Connector used to connect different parts of the coil
    Do not mistake for connectors to other PCB parts (ExternalGeometryConnector)
    This may connect a coil layer spiral to a ExternalGeometryConnector
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
        outside_trace_connector: ExternalGeometryConnector,
        trace_config: TraceConfig,
        layer_rotation_direction: RotationDirection,
        layer: Layer
    ) -> Self:
        """
        Generates connector traces between points trace end and ExternalGeometryConnector,
        it will attempt to generate a seamless connection from trace_end,
        but bridge the gap to ExternalGeometryConnector with a horizontal line
        :param trace_end: endpoint of trace to connect
        :param outisde_trace_connector: center point of ExternalGeometryConnector to connect to
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
        outside_trace_connector: ExternalGeometryConnector,
        trace_config: TraceConfig,
        layer: Layer
    ) -> (Line, Point):
        """
        Generates the horizontal straight line from a 
        outside trace connector towards the coil spiral
        Should be used for generating connectors to ExternalGeometryConnector only
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
        except PointsNotCurvingException:
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

