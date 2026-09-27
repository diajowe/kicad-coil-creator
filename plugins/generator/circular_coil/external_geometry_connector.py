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

This file is intended to provide the structure to connect to geometry
on the pcb that is not part of this footprint
"""

from .via_rings import ViaRingRadius

from ..footprint_objects.via import PadConfig, SolderPad, Via, ViaConfig
from ..helper_classes import Layer, Point, RotationDirection
from ..legacy_kicad_interface import KicadLegacyInterface

class ExternalGeometryConnector(KicadLegacyInterface):
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
        self.center_position = ExternalGeometryConnector._generate_position(
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
            + connecting_via_config.diameter_config.outer_diameter_mm / 2.0 \
            + pad_config.pad_width_mm
        y_offset = connecting_via_config.diameter_config.outer_diameter_mm \
            + pad_config.pad_height_mm

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