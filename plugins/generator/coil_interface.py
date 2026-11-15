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

This file is intended to store structures to unify coil generation
by providing a single interface for all types of coils
"""

from abc import ABC, abstractmethod

import pcbnew

from .exceptions import InvalidLengthException
from .helper_classes import ConfigValueRange, I32_MAX, KICAD_MIN_NOT_NULL, \
    Layer, RotationDirection
from .legacy_kicad_interface import KicadLegacyInterface
from .footprint_objects.trace import TraceConfig
from .footprint_objects.via import ViaDiameterConfig

class CommonCoilConfig:
    """
    Groups together common configuration parameters for all coils
    """

    def __init__(
        self,
        coil_outer_diameter_mm: float,
        rotation_direction: RotationDirection,
        coil_layers: list[Layer],
        turns_per_layer: int,
        ):
        """
        Defines common coil parameters
        :param coil_outer_diameter_mm: Outer diameter of coil, in mm, if coil were perfectly round
        :param rotation_direction: Marks turn direction of coil sprials
        :param coil_layers: Defines the layers the coil should be drawn on, from first to last index
        :param turns_per_layer: How many loops to do on each layer
        :raises InvalidLengthException: If given coil_outer_diameter_mm <= 0
        :raises InvalidLengthException: If given turns_per_layer <= 0
        :raises InvalidLengthException: If given lengh of coil_layers <= 0
        """
        if coil_outer_diameter_mm <= 0:
            raise InvalidLengthException(coil_outer_diameter_mm)
        if len(coil_layers) <= 0:
            raise InvalidLengthException(len(coil_layers))
        if turns_per_layer <= 0:
            raise InvalidLengthException(turns_per_layer)

        self.coil_outer_diameter_mm = coil_outer_diameter_mm
        self.rotation_direction = rotation_direction
        self.coil_layers = coil_layers
        self.turns_per_layer = turns_per_layer

    @classmethod
    def get_outer_diam_range(cls) -> ConfigValueRange:
        """
        Returns the value range of the outer coil diameter config value
        """

        return ConfigValueRange(KICAD_MIN_NOT_NULL, float(I32_MAX))

    @classmethod
    def get_turns_per_layer_range(cls) -> ConfigValueRange:
        """
        Returns the value range of the number of coil loops per layer config value
        """
        return ConfigValueRange(1, I32_MAX)

    @classmethod
    def get_num_layers_range(cls) -> ConfigValueRange:
        """
        Returns the value range of the number of coil layers config value
        """
        return ConfigValueRange(1, pcbnew.GetBoard().GetCopperLayerCount() + 1)

    @classmethod
    def get_outer_diam_default(cls) -> float:
        """
        Returns the default value of the outer coil diameter config value
        """
        return 10.0

    @classmethod
    def get_turns_per_layer_default(cls) -> int :
        """
        Returns the default value of the number of coil loops per layer config value
        """
        return 5

    @classmethod
    def get_num_layers_default(cls) -> int:
        """
        Returns the default value of the number of coil layers config value
        """
        return 1

    @classmethod
    def get_rotation_direction_default(cls) -> RotationDirection:
        """
        Returns the default value for the coil rotation direction config value
        """
        return RotationDirection.CLOCKWISE

    def get_layer_count(self) -> int:
        """
        Returns the number of layer in a coil
        :returns: Number of layers in a coil
        :rtype: int
        """
        return len(self.coil_layers)

class CoilInterface(KicadLegacyInterface, ABC):
    """
    Defines functions to uniformly handle coils and their generation
    """

    @abstractmethod
    def __init__(
        self,
        common_coil_config: CommonCoilConfig,
        trace_config: TraceConfig,
        via_config: ViaDiameterConfig
    ):
        """
        Generates circular coil according to given parameter.
        Does not guarantee that a coil with given parameter will be properly manufacturable
        :param common_coil_config: Parameters all types of coil share
        :param trace_config: Parameters of a trace
        :param via_diameter_config: Configuration for via diameters
        """
