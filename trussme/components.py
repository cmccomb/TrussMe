import abc
from typing import TypedDict, Literal

import numpy

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


class Shape(abc.ABC):
    """
    Abstract base class for shapes, only ever used for typehints.
    """

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
    """
    A class to represent a joint in a truss

    Parameters
    ----------
    coordinates: list[float]
        The coordinates of the joint

    Attributes
    ----------
    idx: int
        The index of the joint
    coordinates: list[float]
        The coordinates of the joint
    translation_restricted: list[bool]
        The translation restrictions of the joint
    loads: list[float]
        The loads on the joint
    members: list[Member]
        The members connected to the joint
    reactions: list[float]
        The reactions at the joint
    deflections: list[float]
        The deflections of the joint

    """

    def __init__(self, coordinates: list[float]):
        # Save the joint id
        self.idx: int = 0

        # Coordinates of the joint
        self.coordinates = coordinates

        # Restricted translation in x, y, and z
        self.translation_restricted: list[bool] = [True, True, True]

        # Loads
        self.loads: list[float] = [0.0, 0.0, 0.0]

        # Store connected members
        self.members: list[Member] = []

        # Loads
        self.reactions: list[float] = [0.0, 0.0, 0.0]

        # Loads
        self.deflections: list[float] = [0.0, 0.0, 0.0]

    def free(self):
        """
        Free translation in all directions

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.translation_restricted = [False, False, False]

    def pinned(self):
        """
        Restrict translation in all directions

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        # Restrict all translation
        self.translation_restricted = [True, True, True]

    def roller(self, constrained_axis: Literal["x", "y", "z"] = "y"):
        """
        Free translation in all directions except one, creating a roller joint

        Parameters
        ----------
        constrained_axis: str, default="y"
            The axis to restrict translation along

        Returns
        -------
        None
        """
        # Only support reaction along denoted axis
        self.translation_restricted = [False, False, False]
        if constrained_axis == "x":
            self.translation_restricted[0] = True
        elif constrained_axis == "y":
            self.translation_restricted[1] = True
        elif constrained_axis == "z":
            self.translation_restricted[2] = True

    def slot(self, free_axis: Literal["x", "y", "z"] = "x"):
        """
        Restricted translation in all directions except one, creating a slot joint

        Parameters
        ----------
        free_axis: str, default="x"
            The axis to allow translation along

        Returns
        -------
        None
        """
        # Only allow translation along denoted axis
        self.translation_restricted = [True, True, True]
        if free_axis == "x":
            self.translation_restricted[0] = False
        elif free_axis == "y":
            self.translation_restricted[1] = False
        elif free_axis == "z":
            self.translation_restricted[2] = False


class Member(object):
    """
    A class to represent a member in a truss

    Parameters
    ----------
    begin_joint: Joint
        The joint at the beginning of the member
    end_joint: Joint
        The joint at the end of the member
    material: Material
        The material used for the member
    shape: Shape
        The shape of the member

    Attributes
    ----------
    idx: int
        The index of the member
    shape: Shape
        The shape of the member
    material: Material
        The material used for the member
    begin_joint: Joint
        The joint at the beginning of the member
    end_joint: Joint
        The joint at the end of the member
    """

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
        """float: The yield strength of the material used in the member"""
        return self.material["yield_strength"]

    @property
    def density(self) -> float:
        """float: The density of the material used in the member"""
        return self.material["density"]

    @property
    def elastic_modulus(self) -> float:
        """float: The elastic modulus of the material used in the member"""
        return self.material["elastic_modulus"]

    @property
    def material_name(self) -> str:
        """float: The name of the material used in the member"""
        return self.material["name"]

    @property
    def moment_of_inertia(self) -> float:
        """float: The moment of inertia of the shape used for the member"""
        return self.shape.moi()

    @property
    def area(self) -> float:
        """float: The cross-sectional area of the shape used for the member"""
        return self.shape.area()

    @property
    def linear_mass(self) -> float:
        """float: The linear mass of the member"""
        return self.area * self.density

    @property
    def length(self) -> float:
        """float: The length of the member"""
        return numpy.linalg.norm(
            numpy.array(self.begin_joint.coordinates)
            - numpy.array(self.end_joint.coordinates)
        )

    @property
    def mass(self) -> float:
        """float: The total mass of the member"""
        return self.length * self.linear_mass

    @property
    def force(self) -> float:
        """float: The force in the member"""
        return self._force

    @force.setter
    def force(self, new_force: float):
        self._force = new_force

    @property
    def fos_yielding(self) -> float:
        """float: The factor of safety against yielding"""
        return self.yield_strength / abs(self.force / self.area)

    @property
    def fos_buckling(self) -> float:
        """float: The factor of safety against buckling"""
        return (
            -(
                (numpy.pi**2)
                * self.elastic_modulus
                * self.moment_of_inertia
                / (self.length**2)
            )
            / self.force
        )
