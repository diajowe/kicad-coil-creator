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

from .legacy_kicad_interface import KicadLegacyInterface

class CoilInterface(KicadLegacyInterface, ABC):
    """
    Defines functions to uniformly handle coils and their generation
    """

    @abstractmethod
    def to_legacy_api_string(self) -> str:
        """
        Converts coil object to legacy string based KiCAD API string,
        intended to be used in footprints
        :return: Legacy KiCAD API string
        :rtype: str
        """
