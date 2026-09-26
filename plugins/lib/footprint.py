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

This file is intended to provide the footprint main structure and its configuration.
See https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html
See https://dev-docs.kicad.org/en/file-formats/sexpr-footprint/index.html
"""

from .helper_classes import Layer, Point
from .legacy_kicad_interface import KicadLegacyInterface
from .coil_interface import CoilInterface


class FootprintProperty(KicadLegacyInterface):
    """
    KiCAD footprint property tag object, consisting of a key value pair
    """

    def __init__(
        self,
        position: Point,
        layer: Layer,
        key: str,
        value: str
        ):
        """
        Generate a footprint property object at a position, on a layer
        :param position: Center position of the object to place
        :param layer: Layer to place property object on
        :param key: Key to use for the property object
        :param value: Value to use for the property object
        """
        self.position = position
        self.layer = layer
        self.key = key
        self.value = value

    def to_legacy_api_string(self) -> str:
        return f"""
	    (property "{self.key}" "{self.value}"
	    	(at {self.position.to_legacy_api_string()})
	    	(unlocked yes)
	    	(layer "{self.layer.to_legacy_api_string()}")
	    	(hide no)
	    	(effects
	    		(font
	    			(size 1 1)
	    			(thickness 0.15)
	    		)
	    	)
	    )
        """

class Footprint(KicadLegacyInterface):
    """
    KiCAD footprint main object
    """

    def __init__(self, name: str, coil: CoilInterface):
        """
        Generate a footprint object representing a coil
        :param name: Name of the coil displayed as parameter
        :param coil: Actual coil to generate on PCB
        """
        self.name = name
        self.coil = coil

    def to_legacy_api_string(self) -> str:
        p1 = FootprintProperty(Point(0.0, 0.0), Layer("F.SilkS", False), "Reference", "REF**")
        p2 = FootprintProperty(Point(0.0, 1.5), Layer("F.Fab", False), "Value", self.name)
        p3 = FootprintProperty(Point(0.0, 0.0), Layer("F.Fab", False), "user", r"${REFERENCE}")
        return f"""
        (footprint "{self.name}" (version 20211014) (generator kicad_coil_generator_plugin)
        	(layer "F.Cu")
        	(attr smd)
            {p1.to_legacy_api_string()}
            {p2.to_legacy_api_string()}
            {p3.to_legacy_api_string()}
        	(zone_connect 2)
        	(net_tie_pad_groups "{self.coil.get_net_tie_string()}")
        	(attr exclude_from_pos_files exclude_from_bom allow_missing_courtyard)
            {self.coil.to_legacy_api_string()}
        )
        """
