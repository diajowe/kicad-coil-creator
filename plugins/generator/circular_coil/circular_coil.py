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

from ..coil_interface import CoilInterface, CommonCoilConfig
from ..footprint_objects.trace import TraceConfig
from ..footprint_objects.via import ViaConfig, ViaDiameterConfig, PadConfig
from ..helper_classes import SpiralPosition

class CircularCoil(CoilInterface):
    """
    Generates round coils
    """

    _DEFAULT_SOLDER_PAD_WIDH_MULTIPLIER: int = 8
    _DEFAULT_UPPER_LAYER_PADNUM: int = 1
    _DEFAULT_LOWER_LAYER_PADNUM: int = 2

    def __init__(
        self,
        common_coil_config: CommonCoilConfig,
        trace_config: TraceConfig,
        via_diameter_config: ViaDiameterConfig
    ):
        """
        Generates circular coil according to given parameters.
        Does not guarantee that a coil with given parameter will be properly manufacturable
        :param common_coil_config: Parameters all types of coil share
        :param trace_config: Parameters of a trace
        :param via_diameter_config: Configuration for via diameters
        """

        connecting_via_config = ViaConfig.get_connecting_via_config(via_diameter_config)

        # generate via rings
        via_radius = ViaRingRadius.get_via_radius_from_coil_params(
            common_coil_config,
            trace_config,
            connecting_via_config
        )
        self.via_rings = ViaRings.get_via_rings_from_settings(
            via_radius,
            ViaRingCount.get_num_vias(common_coil_config),
            connecting_via_config
        )

        # generate net tie string
        self.net_tie_string = \
            f"{ViaConfig.CONNECTING_VIA_PAD_NUM}, \
            {CircularCoil._DEFAULT_UPPER_LAYER_PADNUM}, \
            {CircularCoil._DEFAULT_LOWER_LAYER_PADNUM}" \
            if common_coil_config.get_layer_count() > 1 \
            else \
            f"{CircularCoil._DEFAULT_UPPER_LAYER_PADNUM}, \
            {CircularCoil._DEFAULT_LOWER_LAYER_PADNUM}"

        # generate coil spirals
        self.coil_spirals: list[LayerSpiral] = []
        current_rotation_direction = common_coil_config.rotation_direction

        for layer in common_coil_config.coil_layers:
            # todo: unify radius and diameter everywhere
            self.coil_spirals.append(LayerSpiral.get_layer_spiral(
                common_coil_config.turns_per_layer,
                common_coil_config.coil_outer_diameter_mm / 2.0,
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
                common_coil_config.coil_layers[0],
                upper_connector_via_config,
                PadConfig(
                    CircularCoil._DEFAULT_UPPER_LAYER_PADNUM,
                    pad_width_mm,
                    pad_height_mm
                ),
                common_coil_config.rotation_direction
            )
        )

        # generate lower connector only if layer count for coil is even,
        # else the last connecting via inside needs to be "connector"
        if common_coil_config.get_layer_count() % 2 == 0:
            # todo: setting pad_num directly should be restricted
            # todo: deepcopy feels unclean
            lower_connector_via_config = deepcopy(connecting_via_config)
            lower_connector_via_config.pad_num = CircularCoil._DEFAULT_LOWER_LAYER_PADNUM

            self.outside_connectors.append(
                ExternalGeometryConnector(
                    False,
                    via_radius,
                    common_coil_config.coil_layers[-1],
                    lower_connector_via_config,
                    PadConfig(
                        CircularCoil._DEFAULT_LOWER_LAYER_PADNUM,
                        pad_width_mm,
                        pad_height_mm
                    ),
                    common_coil_config.rotation_direction
                )
            )
        else:
            # todo: this should not be done via direct access of array elements and members
            self.via_rings.inner_vias[-1].config.pad_num = CircularCoil._DEFAULT_LOWER_LAYER_PADNUM

        # generate trace inter connector between all structures to connect layers and coil ends
        self.trace_inner_inter_connectors: list[TraceInterConnector] = []

        current_rotation_direction = common_coil_config.rotation_direction
        for (index, layer) in enumerate(common_coil_config.coil_layers):
            current_inner_trace_end = self.coil_spirals[index].get_end_point(
                SpiralPosition.INSIDE)
            current_outer_trace_end = self.coil_spirals[index].get_end_point(
                SpiralPosition.OUTSIDE)

            current_inner_via = self.via_rings.inner_vias[int(
                index / 2)].get_center_point()

            if index == common_coil_config.get_layer_count()- 1:
                if common_coil_config.get_layer_count() % 2 == 0:
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
