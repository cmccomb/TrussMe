"""
Trussme: A library for truss analysis and design

This library includes some utilities and tools for analyzing and designing truss structures

"""

from .components import (
    material_library,
    Shape,
    Material,
    Pipe,
)  # Box, Pipe, Bar, Square
from .truss import Truss, read_trs, read_json, Goals
