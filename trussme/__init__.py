"""
Trussme: A library for truss analysis and design

This library includes some utilities and tools for analyzing and designing truss structures.

Examples
--------
First, let's construct a small truss
>>> import trussme
>>> small_truss = trussme.Truss()
>>> pin = small_truss.add_pinned_joint([0.0, 0.0, 0.0])
>>> free = small_truss.add_free_joint([2.5, 2.5, 0.0])
>>> roller = small_truss.add_roller_joint([5.0, 0.0, 0.0])
>>> small_truss.add_member(pin, free)
>>> small_truss.add_member(pin, roller)
>>> small_truss.add_member(roller, free)

Since our truss is planar, its important to add out-of-plane support
>>> small_truss.add_out_of_plane_support("z")

Let's add a load to the truss
>>> small_truss.joints[1].loads[1] = -10000

Finally, let's analyze the truss and get the factor of safety and mass
>>> small_truss.analyze()
>>> small_truss.fos
0.958918112668615
>>> small_truss.mass
22.480385653941532
"""

from trussme.components import (
    material_library,
    Shape,
    Material,
    Pipe,
    Box,
    Pipe,
    Bar,
    Square,
)
from trussme.truss import Truss, read_trs, read_json, Goals
from trussme.report import report_to_str, report_to_md, print_report
