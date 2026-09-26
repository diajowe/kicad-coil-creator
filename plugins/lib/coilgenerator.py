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
"""

from .circular_coil import CircularCoil
from .helper_classes import Layer
# todo: this import is kinda wonky
from .footprint import Footprint

# todo: finish, add proper docu
def generate(layer_count, rotation_direction, turns_per_layer, trace_width, trace_spacing, via_diameter, via_drill, outer_diameter, coil_name, layer_names: list[Layer]):
    """
    Generates coils with given parameters. Attempts to place all parts to generate valid coils, though with some parameters, producing a valid coil might not be possible
    Args:
            layer_count: Number of layers in coil
            wrap_clockwise: Clockwise or counter-clockwise coil wrapping
            turns_per_layer: Minimum number of turns per layer: Connecting to vias might introduce up to one more turn
            trace_width: Width of line trace
            trace_spacing: Distance between line traces
            via_diameter: Outer diameter of connecting vias
            via_drill: Diameter of via drill hole
            outer_diameter: Desires outer coil diameter. Coil generation is from outside to inside, so if this is too small, coil wraps may collode
            coil_name: Reference name of coil to put in kicad
            layer_names: Names of Kicad layers to place coil in. Lenght is expected to be >= layer_count
    Returns:
            File: Generated coil in file
    """

    coil = CircularCoil(
        outer_diameter,
        rotation_direction,
        layer_names[:layer_count],
        turns_per_layer,
        trace_width,
        trace_spacing,
        via_diameter,
        via_drill
    )
    return Footprint(coil_name, coil).to_legacy_api_string()


# generate the pads
# NOTE: there are some oddities in KiCAD here. The pad must be sufficiently far away from the last line such that
# KiCAD does not display the "Cannot start routing from a graphic" error. It also must be far enough away that the
# trace does not throw the "The routing start point violates DRC error". I have found that a 0.5mm gap works ok in
# most scenarios, with a 1.2mm wide pad. Feel free to adjust to your needs, but you've been warned.
