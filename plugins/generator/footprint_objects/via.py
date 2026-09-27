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

This file is intended to provide the footprint via structure and its configuration.
Solder pads on footprints are internally also vias
See https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html
"""

from typing import Self
from enum import Enum

from ..exceptions import CoilGenException, InvalidLengthException
from ..helper_classes import Layer, Point, Uuid
from ..legacy_kicad_interface import KicadLegacyInterface

class PadType(Enum):
    """
    Defines type of footprint pad
    """

    THRU_HOLE = "thru_hole"
    SMD = "smd"
    CONNECT = "connect"
    NP_THRU_HOLE = "np_thru_hole"

class PadShape(Enum):
    """
    Defines shape of footprint pad
    """

    CIRCLE = "circle"
    RECT = "rect"
    OVAL = "oval"
    TRAPEZOID = "trapezoid"
    ROUNDRECT = "roundrect"
    CUSTOM = "custom"


class PadNumException(CoilGenException):
    """
    Custom exception raised by a structure generating Pads
    (see this library's SolderPad or Via classes)
    when a pad number was given that is < 0
    """


class ViaException(CoilGenException):
    """
    Custom exception grouping anything together that is related to vias
    (see this library's Via class)
    """

class DiameterMismatchException(ViaException):
    """
    Custom exception being raised when generating a via,
    and the given drill diameter is >= the via's outer diameter.
    This would, when manufactured, drill the via away
    """
    def __init__(self, outer_diameter_mm: float, drill_diameter_mm: float):
        """
        Generates the exception
        :param outer_diameter_mm: Given via outer diameter that is incompatible with drill diameter
        :param drill_diameter_mm: Given via drill diameter that is incompatible with outer diameter
        """
        self.outer_diameter_mm = outer_diameter_mm
        self.drill_diameter_mm = drill_diameter_mm


class ViaDiameterConfig:
    """
    Groups together diameter configuration parameters of vias
    """

    def __init__(self,outer_diameter_mm: float, drill_diameter_mm: float):
        """
        Defines via diameter parameters
        :param outer_diameter_mm: Diameter in mm of entire via. Has to be > drill_diameter_mm
        :param drill_diameter_mm: Diameter in mm of drill hole. Has to be < outer_diameter_mm
        :raises InvalidLengthException: If given outer_diameter_mm or drill_diameter_mm is <= 0
        :raises DiameterMismatchException: If given outer_diameter_mm is <= drill_diameter_mm
        """
        if drill_diameter_mm <= 0 or outer_diameter_mm <= 0:
            raise InvalidLengthException(drill_diameter_mm)
        if outer_diameter_mm <= drill_diameter_mm:
            raise DiameterMismatchException(outer_diameter_mm, drill_diameter_mm)

        self.outer_diameter_mm = outer_diameter_mm
        self.drill_diameter_mm = drill_diameter_mm

class ViaConfig:
    """
    Groups together configuration parameters of vias
    """

    CONNECTING_VIA_PAD_NUM: int = 0

    def __init__(self, pad_num: int, via_diameter_config: ViaDiameterConfig):
        """
        Defines via parameters
        :param pad_num: Number of pad >= 0, should be unique for all used pads in footprint
        :param via_diameter_config: Configuration parameters for via diameters
        :raises PadNumException: If given pad_num is < 0
        """
        if pad_num < 0:
            raise PadNumException(pad_num)
        self.pad_num = pad_num
        self.diameter_config = via_diameter_config

    @classmethod
    def get_connecting_via_config(cls, via_diameter_config: ViaDiameterConfig) -> Self:
        """
        Defines via parameters for connecting vias (where pad number is static)
        Connecting vias interconnect parts of a coil (contrary to outside connectors)
        :param via_diameter_config: Configuration parameters for via diameters
        :return: Parameters for connecting vias
        :rtype: ViaConfig
        """

        return ViaConfig(ViaConfig.CONNECTING_VIA_PAD_NUM, via_diameter_config)


class PadConfig:
    """
    Groups together configuration parameters of smd pads
    """

    def __init__(self, pad_num: int, pad_width_mm: float, pad_height_mm: float):
        """
        Defines pad parameters
        :param pad_num: Number of pad >= 0, should be unique for all used pads in footprint
        :param pad_width_mm: Desired width of a possible connector pad > 0
        :param pad_height_mm: Desired height of a possible connector pad > 0
        :raises PadNumException: If given pad_num is < 0
        :raises InvalidLengthException: If given pad_width_mm or pad_heigh_mm is <= 0
        """
        if pad_num < 0:
            raise PadNumException(pad_num)
        if pad_width_mm <= 0:
            raise InvalidLengthException(pad_width_mm)
        if pad_height_mm <= 0:
            raise InvalidLengthException(pad_height_mm)

        self.pad_num = pad_num
        self.pad_width_mm = pad_width_mm
        self.pad_height_mm = pad_height_mm


class Via(KicadLegacyInterface):
    """
    KiCAD footprint via object
    """

    def __init__(self, position: Point, config: ViaConfig):
        """
        Generate a via at a position
        :param position: Center position of the via
        :param config: Configuration parameters of via
        """
        self.position = position
        self.config = config

    def get_center_point(self) -> Point:
        """
        Returns the center point of this via
        :returns: Center point of the via
        :rtype: Point
        """
        return self.position

    def to_legacy_api_string(self) -> str:
        return f"""
        (pad "{self.config.pad_num}" {PadType.THRU_HOLE.value} {PadShape.CIRCLE.value}
    		(at {self.position.to_legacy_api_string()})
    		(size {self.config.diameter_config.outer_diameter_mm} {self.config.diameter_config.outer_diameter_mm})
    		(drill {self.config.diameter_config.drill_diameter_mm})
    		(layers *.Cu)
    		(remove_unused_layers yes)
    		(keep_end_layers yes)
    		(uuid {Uuid().to_legacy_api_string()})
    	)
        """

class SolderPad(KicadLegacyInterface):
    """
    KiCAD footprint solder pad object
    """

    def __init__(
        self,
        position: Point,
        pad_config: PadConfig,
        layer: Layer
        ):
        """
        Generate a solder pad at a position
        :param position: Center position of the solder pad
        :param pad_config: Configuration parameters of the pad
        :param layer: PCB layer to place line on
        """

        self.position = position
        self.config = pad_config
        self.layer = layer

    def to_legacy_api_string(self) -> str:
        return f"""
        (pad "{self.config.pad_num}" {PadType.SMD.value} {PadShape.ROUNDRECT.value}
        	(at {self.position.to_legacy_api_string()})
        	(size {self.config.pad_width_mm:.3f} {self.config.pad_height_mm:.3f})
        	(layers "{self.layer.to_legacy_api_string()}")
        	(roundrect_rratio 0.25)
        	(uuid {Uuid().to_legacy_api_string()})
        )
        """
