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

This file is intended to store custom exception bases for exceptions thrown by this library
"""
# todo: move these exceptions to the proper area
from typing import Union

class CoilGenException(Exception):
    """
    Base exception class where all custom exceptions should derive from
    """

class CoilGenValueException(CoilGenException):
    """
    Custom exception that serves the same purpose as python's builtin ValueError,
    but restricted to int or float
    :param value: Invalid value received
    """
    def __init__(self, value: Union[int, float]):
        self.value = value

class InvalidLengthException(CoilGenValueException):
    """
    Custom exception raised when a length <= 0 was given, but a value > 0 was expected
    """

