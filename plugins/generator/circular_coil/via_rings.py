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

This file is intended to provide the structure to arrange
vias on the circular coil. These vias are used to connect coil parts
"""

from math import radians, sin, sqrt
from typing import Self

# todo: is deepcopy needed
from copy import deepcopy

from ..footprint_objects.trace import TraceConfig
from ..footprint_objects.via import Via, ViaConfig
from ..exceptions import CoilGenException, InvalidLengthException
from ..helper_classes import Point
from ..legacy_kicad_interface import KicadLegacyInterface
from ..coil_interface import CommonCoilConfig

class ViaRingsException(CoilGenException):
    """
    Custom exception grouping anything together that is related to via rings
    on circular coils
    (see this library's ViaRings class)
    """

class ViaRingCount:
    """
    Stores number of vias on each of the two via rings
    """

    def __init__(self, inner_ring_num: int, outer_ring_num: int):
        if inner_ring_num < 0 or outer_ring_num < 0:
            raise ViaRingsException()

        self.inner_ring_num = inner_ring_num
        self.outer_ring_num = outer_ring_num

    @classmethod
    def get_num_vias(cls, common_coil_config: CommonCoilConfig) -> Self:
        """
        Calculates number of vias required on each via ring
        :param common_coil_config: Common coil parameter settings, to extract layer count
        :return: Correlation of how many vias per ring
        :rtype: ViaRingCount
        """
        # coils with uneven layer count need one extra via
        # that allows connection of the coil endpoint as
        # that coil end point would be inside the coil and
        # we do not place solder pads inside the coil
        num_vias = common_coil_config.get_layer_count() \
            - (1 - common_coil_config.get_layer_count() % 2)
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
        common_coil_config: CommonCoilConfig,
        trace_config: TraceConfig,
        connecting_via_config: ViaConfig,
    ) -> Self:
        """
        Calculates diameter at which vias need to be placed.
        Vias are placed alternating on an inner circle and an outer circle
        :param common_coil_config: Parameters all types of coil share
        :param trace_config: Parameters of a trace
        :param connecting_via_config: Configuration for connecting vias
        :return: Calculated rings to place connecting vias on
        :rtype: ViaRingRadius
        """
        coil_outer_radius_mm = common_coil_config.coil_outer_diameter_mm / 2.0
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
            - common_coil_config.turns_per_layer * trace_config.trace_width_mm \
            - common_coil_config.turns_per_layer * trace_config.trace_spacing_mm \
            - (connecting_via_config.diameter_config.outer_diameter_mm / 2) \
            - (0.5 * trace_config.trace_width_mm) \
            - 2 * (trace_config.trace_spacing_mm + trace_config.trace_width_mm)

        # starting from the outer radius of the coil traces
        # we need to add the via radius or else the via ring will sit on a coil loop.
        # we add two more trace width and space beetween traces to create a bit of breathing space
        # and prevent via edge to collide with loop traces
        via_outer_ring_radius_mm = coil_outer_radius_mm \
            + (connecting_via_config.diameter_config.outer_diameter_mm / 2) \
            + 2 * (trace_config.trace_spacing_mm + trace_config.trace_width_mm)

        return ViaRingRadius(via_inner_ring_radius_mm, via_outer_ring_radius_mm)

class InvalidViaCountException(ViaRingsException):
    """
    Custom exception being raised when generating a via ring,
    and the given number of vias to generate is < 0
    """

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
            raise InvalidLengthException(radius)
        if num_on_ring < 0:
            raise InvalidViaCountException()

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

