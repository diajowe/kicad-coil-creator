"""
This script is used to generate pcb coils
Copyright (C) 2022 Colton Baldridge
Copyright (C) 2023 Tim Goll

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

This file is intended to give an entry point to generating coils of all types
"""

from .circular_coil import CircularCoil
from .coil_interface import CommonCoilConfig
from .footprint import Footprint
from .footprint_objects.trace import TraceConfig
from .footprint_objects.via import ViaDiameterConfig
from .helper_classes import Layer

def generate(
    coil_name: str,
    common_coil_config: CommonCoilConfig,
    trace_config: TraceConfig,
    via_diameter_config: ViaDiameterConfig
    ):
    """
    Generates (currently) circular coil according to given parameters.
    Later should be used for generating other type of coils too
    Does not guarantee that a coil with given parameter will be properly manufacturable
    :param coil_name: Name of the coil to be used in PCB
    :param common_coil_config: Parameters all types of coil share
    :param trace_config: Parameters of a trace
    :param via_diameter_config: Configuration for via diameters
    """

    coil = CircularCoil(common_coil_config, trace_config, via_diameter_config)
    return Footprint(coil_name, coil).to_legacy_api_string()
