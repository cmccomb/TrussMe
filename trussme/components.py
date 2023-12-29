import abc
from typing import TypedDict, Literal

import numpy

g: float = 9.80665
"""float: Gravitational constant for computing weight from mass
"""

Material = TypedDict(
    "Material",
    {
        "name": str,
        "density": float,
        "elastic_modulus": float,
        "yield_strength": float,
    },
)
"""TypedDict: New type to contain material properties"""

material_library: list[Material] = [
    {
        "name": "A36_Steel",
        "density": 7800.0,
        "elastic_modulus": 200 * pow(10, 9),
        "yield_strength": 250 * pow(10, 6),
    },
    {
        "name": "A992_Steel",
        "density": 7800.0,
        "elastic_modulus": 200 * pow(10, 9),
        "yield_strength": 345 * pow(10, 6),
    },
    {
        "name": "6061_T6_Aluminum",
        "density": 2700.0,
        "elastic_modulus": 68.9 * pow(10, 9),
        "yield_strength": 276 * pow(10, 6),
    },
]
"""list[Material]: List of built-in materials to choose from
"""

NewShape = TypedDict(
    "NewShape",
    {
        "name": str,
        "moment_of_inertia": float,
        "area": float,
    },
)
"""TypedDict: New type to contain shape properties"""


class Shape(abc.ABC):
    """Abstract base class for shapes, only ever used for typehints."""

    @abc.abstractmethod
    def __init__(self):
        self.w = None
        self.h = None
        self.t = None
        self.r = None

    @abc.abstractmethod
    def moi(self) -> float:
        pass

    @abc.abstractmethod
    def area(self) -> float:
        pass

    @abc.abstractmethod
    def name(self) -> str:
        pass


class Pipe(Shape):
    def __init__(self, r: float = 0.0, t: float = 0.0):
        self.r: float = r
        self.t: float = t
        self.w = None
        self.h = None

    def moi(self) -> float:
        return (numpy.pi / 4.0) * (self.r**4 - (self.r - 2 * self.t) ** 4)

    def area(self) -> float:
        return numpy.pi * (self.r**2 - (self.r - self.t) ** 2)

    def name(self) -> str:
        return "pipe"


class Bar(Shape):
    def __init__(self, r: float = 0.0):
        self.r: float = r
        self.w = None
        self.h = None
        self.t = None

    def moi(self) -> float:
        return (numpy.pi / 4.0) * self.r**4

    def area(self) -> float:
        return numpy.pi * self.r**2

    def name(self) -> str:
        return "bar"


class Square(Shape):
    def __init__(self, w: float = 0.0, h: float = 0.0):
        self.w: float = w
        self.h: float = h
        self.t = None
        self.r = None

    def moi(self) -> float:
        if self.h > self.w:
            return (1.0 / 12.0) * self.w * self.h**3
        else:
            return (1.0 / 12.0) * self.h * self.w**3

    def area(self) -> float:
        return self.w * self.h

    def name(self) -> str:
        return "square"


class Box(Shape):
    def __init__(self, w: float = 0.0, h: float = 0.0, t: float = 0.0):
        self.w: float = w
        self.h: float = h
        self.t: float = t
        self.r = None

    def moi(self) -> float:
        if self.h > self.w:
            return (1.0 / 12.0) * (self.w * self.h**3) - (1.0 / 12.0) * (
                self.w - 2 * self.t
            ) * (self.h - 2 * self.t) ** 3
        else:
            return (1.0 / 12.0) * (self.h * self.w**3) - (1.0 / 12.0) * (
                self.h - 2 * self.t
            ) * (self.w - 2 * self.t) ** 3

    def area(self) -> float:
        return self.w * self.h - (self.h - 2 * self.t) * (self.w - 2 * self.t)

    def name(self) -> str:
        return "box"


class Joint(object):
    def __init__(self, coordinates: list[float]):
        # Save the joint id
        self.idx: int = 0

        # Coordinates of the joint
        self.coordinates = coordinates

        # Allowed translation in x, y, and z
        self.translation: list[bool] = [True, True, True]

        # Loads
        self.loads: list[float] = [0.0, 0.0, 0.0]

        # Store connected members
        self.members: list[Member] = []

        # Loads
        self.reactions: list[float] = [0.0, 0.0, 0.0]

        # Loads
        self.deflections: list[float] = [0.0, 0.0, 0.0]

    def free(self, d: int = 3):
        self.translation = [False, False, False]
        # If 2d, add out of plane support
        if d == 2:
            self.translation[2] = True

    def pinned(self):
        # Restrict all translation
        self.translation = [True, True, True]

    def roller(self, axis: Literal["x", "y"] = "y", d: int = 3):
        # Only support reaction along denoted axis
        self.translation = [False, False, False]
        self.translation[ord(axis) - 120] = True

        # If 2d, add out of plane support
        if d == 2:
            self.translation[2] = True


class Member(object):
    def __init__(
        self, begin_joint: Joint, end_joint: Joint, material: Material, shape: Shape
    ):
        # Save id number
        self.idx: int = 0

        # Shape independent variables
        self.shape: Shape = shape

        # Material properties
        self.material: Material = material

        # Variables to store information about truss state
        self._force: float = 0

        # Variable to store location in truss
        self.begin_joint: Joint = begin_joint
        self.end_joint: Joint = end_joint

    @property
    def yield_strength(self) -> float:
        return self.material["yield_strength"]

    @property
    def density(self) -> float:
        return self.material["density"]

    @property
    def elastic_modulus(self) -> float:
        return self.material["elastic_modulus"]

    @property
    def material_name(self) -> str:
        return self.material["name"]

    @property
    def moment_of_inertia(self) -> float:
        return self.shape.moi()

    @property
    def area(self) -> float:
        return self.shape.area()

    @property
    def linear_weight(self) -> float:
        return self.area * self.density

    @property
    def length(self) -> float:
        return numpy.linalg.norm(
            numpy.array(self.begin_joint.coordinates)
            - numpy.array(self.end_joint.coordinates)
        )

    @property
    def mass(self) -> float:
        return self.length * self.linear_weight

    @property
    def force(self) -> float:
        return self._force

    @force.setter
    def force(self, new_force: float):
        self._force = new_force

    @property
    def fos_yielding(self) -> float:
        return self.yield_strength / abs(self.force / self.area)

    @property
    def fos_buckling(self) -> float:
        return (
            -(
                (numpy.pi**2)
                * self.elastic_modulus
                * self.moment_of_inertia
                / (self.length**2)
            )
            / self.force
        )
