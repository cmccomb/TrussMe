"""
Trussme: A library for truss analysis and design

This library includes some utilities and tools for analyzing and designing truss structures.

Examples
--------
```
import trussme

# Build a small, simple truss
truss = trussme.Truss()
pin = truss.add_pinned_joint([0.0, 0.0, 0.0])
free = truss.add_free_joint([2.5, 2.5, 0.0])
roller = truss.add_roller_joint([5.0, 0.0, 0.0])
truss.add_member(pin, free)
truss.add_member(pin, roller)
truss.add_member(roller, free)

# Add out of plane support and a load
truss.add_out_of_plane_support("z")
truss.joints[1].loads[1] = -10000

# Define goals
goals = trussme.Goals(
    minimum_fos_buckling=1.5,
    minimum_fos_yielding=1.5,
    maximum_mass=5.0,
    maximum_deflection=6e-3,
)

# Print results
trussme.print_report(truss, goals)
```
"""

from .components import material_library, Shape, Material, Pipe, Box, Pipe, Bar, Square
from .truss import Truss, read_trs, read_json, Goals
from .report import report_to_str, report_to_md
