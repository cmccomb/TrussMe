import unittest

import trussme


class TestCustomStuff(unittest.TestCase):
    def test_custom_material(self):
        # Build truss from scratch
        truss = trussme.Truss()
        truss.add_pinned_support([0.0, 0.0, 0.0])
        truss.add_joint([2.5, 2.5, 0.0], d=2)
        truss.add_roller_support([5.0, 0.0, 0.0], d=2)

        truss.joints[1].loads[1] = -20000

        unobtanium: trussme.Material = {
            "name": "unobtanium",
            "yield_strength": 200_000_000_000,
            "elastic_modulus": 200_000_000_000_000.0,
            "density": 1_000.0,
        }

        truss.add_member(0, 1, material=unobtanium)
        truss.add_member(1, 2, material=unobtanium)
        truss.add_member(2, 0, material=unobtanium)

        truss.print_report()

    def test_custom_shape(self):
        # Build truss from scratch
        truss = trussme.Truss()
        truss.add_pinned_support([0.0, 0.0, 0.0])
        truss.add_joint([2.5, 2.5, 0.0], d=2)
        truss.add_roller_support([5.0, 0.0, 0.0], d=2)

        truss.joints[1].loads[1] = -20000

        class MagicalRod(trussme.Shape):

            def __init__(self):
                self.h = None
                self.w = None
                self.r = None
                self.t = None

            def moi(self) -> float:
                return 200_000_000_000

            def area(self) -> float:
                return 200_000_000_000

            def name(self) -> str:
                return "magical rod"

        truss.add_member(0, 1, shape=MagicalRod())
        truss.add_member(1, 2, shape=MagicalRod())
        truss.add_member(2, 0, shape=MagicalRod())

        truss.print_report()