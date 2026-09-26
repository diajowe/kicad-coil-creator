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

This file is intended to store the main structure to generate circular coils.
"""

# todo: is deepcopy needed
from copy import deepcopy

from .external_geometry_connector import ExternalGeometryConnector
from .layer_spiral import LayerSpiral
from .trace_inter_connector import TraceInterConnector
from .via_rings import ViaRingCount, ViaRingRadius, ViaRings

from ..exceptions import InvalidLengthException
from ..footprint_objects.trace import TraceConfig
from ..footprint_objects.via import ViaConfig, PadConfig
from ..helper_classes import Layer, RotationDirection, SpiralPosition
from ..legacy_kicad_interface import KicadLegacyInterface

class CircularCoil(KicadLegacyInterface):
    """
    Generates round coils
    """

    _DEFAULT_SOLDER_PAD_WIDH_MULTIPLIER: int = 8
    _DEFAULT_UPPER_LAYER_PADNUM: int = 1
    _DEFAULT_LOWER_LAYER_PADNUM: int = 2

    def __init__(
        self,
        coil_outer_diameter_mm: float,
        rotation_direction: RotationDirection,
        coil_layers: list[Layer],
        turns_per_layer: int,
        trace_width_mm: float,
        trace_spacing_mm: float,
        via_outer_diameter_mm: float,
        via_drill_diameter_mm: float,
    ):
        """
        Generates circular coil according to given parameter.
        Does not guarantee that a coil with given parameter will be properly manufacturable
        :param coil_outer_diameter_mm: Outer diameter of coil, in mm, if coil were perfectly round
        :param rotation_direction: Marks turn direction of coil sprials
        :param coil_layers: Defines the layers the coil should be drawn on, from first to last index
        :param turns_per_layer: How many loops to do on each layer
        :param trace_width_mm: Width of the drawn trace in mm
        :param trace_spacing_mm: Desired spacing in mm in between traces of a coil spiral
        :param via_outer_diameter_mm: Outer connecting via diameter in mm
        :param via_drill_diameter_mm: Drill hole diameter of connecting via
        """
        # todo : do not raise those on your own, have config objects do that
        if coil_outer_diameter_mm <= 0:
            raise InvalidLengthException(coil_outer_diameter_mm)
        if via_outer_diameter_mm <= 0:
            raise InvalidLengthException(via_outer_diameter_mm)
        if via_drill_diameter_mm <= 0:
            raise InvalidLengthException(via_drill_diameter_mm)
        if len(coil_layers) <= 0:
            raise InvalidLengthException(len(coil_layers))
        if turns_per_layer <= 0:
            raise InvalidLengthException(turns_per_layer)
        if trace_spacing_mm <= 0:
            raise InvalidLengthException(trace_spacing_mm)
        if trace_width_mm <= 0:
            raise InvalidLengthException(trace_width_mm)

        connecting_via_config = ViaConfig.get_connecting_via_config(
            via_outer_diameter_mm,
            via_drill_diameter_mm
        )

        trace_config = TraceConfig(trace_width_mm, trace_spacing_mm)

        # generate via rings
        via_radius = ViaRingRadius.get_via_radius_from_coil_params(
            coil_outer_diameter_mm / 2.0,
            turns_per_layer,
            trace_config,
            connecting_via_config
        )
        self.via_rings = ViaRings.get_via_rings_from_settings(
            via_radius,
            ViaRingCount.get_num_vias(len(coil_layers)),
            connecting_via_config
        )

        # generate net tie string
        self.net_tie_string = \
            f"{ViaConfig.CONNECTING_VIA_PAD_NUM}, \
            {CircularCoil._DEFAULT_UPPER_LAYER_PADNUM}, \
            {CircularCoil._DEFAULT_LOWER_LAYER_PADNUM}" \
            if len(coil_layers) > 1 \
            else \
            f"{CircularCoil._DEFAULT_UPPER_LAYER_PADNUM}, \
            {CircularCoil._DEFAULT_LOWER_LAYER_PADNUM}"

        # generate coil spirals
        self.coil_spirals: list[LayerSpiral] = []
        current_rotation_direction = rotation_direction

        for layer in coil_layers:
            # todo: unify radius and diameter everywhere
            self.coil_spirals.append(LayerSpiral.get_layer_spiral(
                turns_per_layer,
                coil_outer_diameter_mm / 2.0,
                trace_config,
                layer,
                current_rotation_direction
            ))

            # every layer, rotation direction as seen from outside to inside needs to be switched
            # to generate a continuous same direction turn through all layers
            current_rotation_direction = current_rotation_direction.change_rotation_direction()

        # generate connectors to outside structures
        self.outside_connectors: list[ExternalGeometryConnector] = []

        # pads are wider than higher.
        # we simply use trace with as height, so horizontal connection off of pad looks nice
        # and scale the width according to a multiplier with the trace width
        # todo: let this be calculated by dedicated class?
        pad_width_mm = CircularCoil._DEFAULT_SOLDER_PAD_WIDH_MULTIPLIER * \
            trace_config.trace_width_mm
        pad_height_mm = trace_config.trace_width_mm

        # generate upper connector
        # todo: setting pad_num directly should be restricted
        upper_connector_via_config = deepcopy(connecting_via_config)
        upper_connector_via_config.pad_num = CircularCoil._DEFAULT_UPPER_LAYER_PADNUM

        self.outside_connectors.append(
            ExternalGeometryConnector(
                True,
                via_radius,
                coil_layers[0],
                upper_connector_via_config,
                PadConfig(
                    CircularCoil._DEFAULT_UPPER_LAYER_PADNUM,
                    pad_width_mm,
                    pad_height_mm
                ),
                rotation_direction
            )
        )

        # generate lower connector only if layer count for coil is even,
        # else the last connecting via inside needs to be "connector"
        if len(coil_layers) % 2 == 0:
            # todo: setting pad_num directly should be restricted
            # todo: deepcopy feels unclean
            lower_connector_via_config = deepcopy(connecting_via_config)
            lower_connector_via_config.pad_num = CircularCoil._DEFAULT_LOWER_LAYER_PADNUM

            self.outside_connectors.append(
                ExternalGeometryConnector(
                    False,
                    via_radius,
                    coil_layers[-1],
                    lower_connector_via_config,
                    PadConfig(
                        CircularCoil._DEFAULT_LOWER_LAYER_PADNUM,
                        pad_width_mm,
                        pad_height_mm
                    ),
                    rotation_direction
                )
            )
        else:
            # todo: this should not be done via direct access of array elements and members
            self.via_rings.inner_vias[-1].config.pad_num = CircularCoil._DEFAULT_LOWER_LAYER_PADNUM

        # generate trace inter connector between all structures to connect layers and coil ends
        self.trace_inner_inter_connectors: list[TraceInterConnector] = []

        current_rotation_direction = rotation_direction
        for (index, layer) in enumerate(coil_layers):
            current_inner_trace_end = self.coil_spirals[index].get_end_point(
                SpiralPosition.INSIDE)
            current_outer_trace_end = self.coil_spirals[index].get_end_point(
                SpiralPosition.OUTSIDE)

            current_inner_via = self.via_rings.inner_vias[int(
                index / 2)].get_center_point()

            if index == len(coil_layers) - 1:
                if len(coil_layers) % 2 == 0:
                    self.trace_inner_inter_connectors.append(
                        TraceInterConnector.get_connector_for_spiral_to_outside_trace_connector(
                            current_outer_trace_end,
                            self.outside_connectors[1],
                            trace_config,
                            current_rotation_direction,
                            layer
                        )
                    )
            elif index == 0:
                self.trace_inner_inter_connectors.append(
                    TraceInterConnector.get_connector_for_spiral_to_outside_trace_connector(
                        current_outer_trace_end,
                        self.outside_connectors[0],
                        trace_config,
                        current_rotation_direction,
                        layer
                    )
                )
            else:
                current_outer_via = self.via_rings.outer_vias[int(
                    (index - 1) / 2)].get_center_point()
                self.trace_inner_inter_connectors.append(
                    TraceInterConnector.get_connector_for_spiral_to_spiral_via(
                        current_outer_trace_end,
                        current_outer_via,
                        trace_config,
                        current_rotation_direction,
                        SpiralPosition.OUTSIDE,
                        layer
                    )
                )

            self.trace_inner_inter_connectors.append(
                TraceInterConnector.get_connector_for_spiral_to_spiral_via(
                    current_inner_trace_end,
                    current_inner_via,
                    trace_config,
                    current_rotation_direction,
                    SpiralPosition.INSIDE,
                    layer
                )
            )

            # every layer, rotation direction as seen from outside to inside needs to be switched
            # to generate a continuous same direction turn through all layers
            current_rotation_direction = current_rotation_direction.change_rotation_direction()

    def get_net_tie_string(self) -> str:
        """
        Returns the net tie string for coil pads
        :returns: Net tie string for used coil pads
        :rtype: str
        """
        return self.net_tie_string

    def to_legacy_api_string(self) -> str:
        out = ""
        out += self.via_rings.to_legacy_api_string()
        for s in self.coil_spirals:
            out += s.to_legacy_api_string()
        for c in self.outside_connectors:
            out += c.to_legacy_api_string()
        for t in self.trace_inner_inter_connectors:
            out += t.to_legacy_api_string()
        return out
