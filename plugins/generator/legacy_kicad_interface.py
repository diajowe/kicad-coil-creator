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

This file is intended to store structures to aid transforming code objects
to KiCAD objects, using the KiCAD legacy string based API
"""

from abc import ABC, abstractmethod

class KicadLegacyInterface(ABC):
    """
    Defines functions to convert python objects to KiCAD objects
    using the legacy string based API
    """

    @abstractmethod
    def to_legacy_api_string(self) -> str:
        """
        Converts python object to legacy string based KiCAD API string
        :return: Legacy KiCAD API string
        :rtype: str
        """
