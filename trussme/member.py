import numpy
from trussme.joint import Joint
from typing import Union, TypedDict


# Gravitational constant for computing weight from mass
g: float = 9.80665


Material = Union[
    TypedDict("Material", {
        "name": str,
        "density": float,
        "elastic_modulus": float,
        "yield_strength": float,
    }),
    None
]


# Material properties
MATERIALS: list[Material] = [
    {
        "name": "A36_Steel",
        "density": 7800.0,
        "elastic_modulus":   200*pow(10, 9),
        "yield_strength":  250*pow(10, 6)
    },
    {
        "name": "A992_Steel",
        "density": 7800.0,
        "elastic_modulus":   200*pow(10, 9),
        "yield_strength":  345*pow(10, 6)
    },
    {
        "name": "6061_T6_Aluminum",
        "density": 2700.0,
        "elastic_modulus":   68.9*pow(10, 9),
        "yield_strength":  276*pow(10, 6)
    }
]


class Pipe(object):
    def __init__(self, r: float = 0.0, t: float = 0.0):
        self.r: float = r
        self.t: float = t
        self.w = "N/A"
        self.h = "N/A"

    def moi(self) -> float:
        return (numpy.pi / 4.) * (self.r ** 4 - (self.r - 2 * self.t) ** 4)

    def area(self) -> float:
        return numpy.pi * (self.r ** 2 - (self.r - self.t) ** 2)

    def to_str(self) -> str:
        return "pipe"


class Bar(object):
    def __init__(self, r: float = 0.0):
        self.r: float = r
        self.w = "N/A"
        self.h = "N/A"
        self.t = "N/A"

    def moi(self) -> float:
        return (numpy.pi / 4.) * self.r ** 4

    def area(self) -> float:
        return numpy.pi*self.r**2

    def to_str(self) -> str:
        return "bar"


class Square(object):
    def __init__(self, w: float = 0.0, h: float = 0.0):
        self.w: float = w
        self.h: float = h
        self.t = "N/A"
        self.r = "N/A"

    def moi(self) -> float:
        if self.h > self.w:
            return (1./12.)*self.w*self.h**3
        else:
            return (1./12.)*self.h*self.w**3

    def area(self) -> float:
        return self.w * self.h

    def to_str(self) -> str:
        return "square"


class Box(object):
    def __init__(self, w: float = 0.0, h: float = 0.0, t: float = 0.0):
        self.w: float = w
        self.h: float = h
        self.t: float = t
        self.r = "N/A"

    def moi(self) -> float:
        if self.h > self.w:
            return (1./12.)*(self.w*self.h**3)\
                - (1./12.)*(self.w - 2*self.t)*(self.h - 2*self.t)**3
        else:
            return (1./12.)*(self.h*self.w**3)\
                - (1./12.)*(self.h - 2*self.t)*(self.w - 2*self.t)**3

    def area(self) -> float:
        return self.w*self.h - (self.h - 2*self.t)*(self.w - 2*self.t)

    def to_str(self) -> str:
        return "box"


Shape = Union[Pipe, Bar, Square, Box, None]


class Member(object):

    def __init__(self, joint_a: Joint, joint_b: Joint):
        # Save id number
        self.idx = -1

        # Shape independent variables
        self.shape: Shape = None

        # Material properties
        self.material: Material = None

        # Variables to store information about truss state
        self._force: float = 0

        # Variable to store location in truss
        self.joints = [joint_a, joint_b]

        # Calculate properties
        self.set_shape(Pipe(t=0.002, r=0.02))
        self.set_material(MATERIALS[0])

    def set_shape(self, new_shape: Shape):
        self.shape = new_shape

    def set_material(self, new_material: Material):
        # Set material properties
        self.material = new_material

    @property
    def moment_of_inertia(self) -> float:
        return self.shape.moi()

    @property
    def area(self) -> float:
        return self.shape.area()

    @property
    def linear_weight(self) -> float:
        return self.area * self.material["density"]

    @property
    def length(self) -> float:
        return numpy.linalg.norm(self.joints[0].coordinates - self.joints[1].coordinates)

    @property
    def mass(self) -> float:
        return self.length*self.linear_weight

    @property
    def force(self) -> float:
        return self._force

    @force.setter
    def force(self, new_force):
        self._force = new_force

    @property
    def fos_yielding(self) -> float:
        return self.material["yield_strength"] / abs(self.force / self.area)

    @property
    def fos_buckling(self) -> float:
        return -((numpy.pi**2)*self.material["elastic_modulus"]*self.moment_of_inertia
                             /(self.length**2))/self.force