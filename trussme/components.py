import abc
from typing import TypedDict, Literal

import numpy
from numpy.typing import NDArray

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
        self._params = {}

    @abc.abstractmethod
    def moi(self) -> float:
        """
        The moment of inertia of the shape

        Returns
        -------
        float
            The moment of inertia of the shape
        """
        pass

    @abc.abstractmethod
    def area(self) -> float:
        """
        The cross-sectional area of the shape

        Returns
        -------
        float
            The cross-sectional area of the shape
        """
        pass

    @abc.abstractmethod
    def name(self) -> str:
        """
        The name of the shape

        Returns
        -------
        str
            The name of the shape
        """
        pass


class Pipe(Shape):
    """
    A class to represent a pipe, defined by an outer radius, `r`, and a thickness, `t`.

    Parameters
    ----------
    r: float
        The outer radius of the pipe
    t: float
        The thickness of the pipe
    """

    def __init__(self, r: float, t: float):
        self._params = {"r": r, "t": t}

    def moi(self) -> float:
        return (numpy.pi / 4.0) * (
            self._params["r"] ** 4 - (self._params["r"] - 2 * self._params["t"]) ** 4
        )

    def area(self) -> float:
        return numpy.pi * (
            self._params["r"] ** 2 - (self._params["r"] - self._params["t"]) ** 2
        )

    def name(self) -> str:
        return "pipe"


class Bar(Shape):
    """
    A class to represent a solid round bar, defined by a radius, `r`.

    Parameters
    ----------
    r: float
        The radius of the bar
    """

    def __init__(self, r: float):
        self._params = {"r": r}

    def moi(self) -> float:
        return (numpy.pi / 4.0) * self._params["r"] ** 4

    def area(self) -> float:
        return numpy.pi * self._params["r"] ** 2

    def name(self) -> str:
        return "bar"


class Square(Shape):
    """
    A class to represent a square bar, defined by a width, `w`, and a height, `h`.

    Parameters
    ----------
    w: float
        The width of the bar
    h: float
        The height of the bar
    """

    def __init__(self, w: float = 0.0, h: float = 0.0):
        self._params = {"w": w, "h": h}

    def moi(self) -> float:
        if self._params["h"] > self._params["w"]:
            return (1.0 / 12.0) * self._params["w"] * self._params["h"] ** 3
        else:
            return (1.0 / 12.0) * self._params["h"] * self._params["w"] ** 3

    def area(self) -> float:
        return self._params["w"] * self._params["h"]

    def name(self) -> str:
        return "square"


class Box(Shape):
    """
    A class to represent a box, defined by a width, `w`, a height, `h`, and a thickness, `t`.

    Parameters
    ----------
    w: float
        The width of the box
    h: float
        The height of the box
    t: float
        The thickness of the box
    """

    def __init__(self, w: float, h: float, t: float):
        self._params = {"w": w, "h": h, "t": t}

    def moi(self) -> float:
        if self._params["h"] > self._params["w"]:
            return (1.0 / 12.0) * (self._params["w"] * self._params["h"] ** 3) - (
                1.0 / 12.0
            ) * (self._params["w"] - 2 * self._params["t"]) * (
                self._params["h"] - 2 * self._params["t"]
            ) ** 3
        else:
            return (1.0 / 12.0) * (self._params["h"] * self._params["w"] ** 3) - (
                1.0 / 12.0
            ) * (self._params["h"] - 2 * self._params["t"]) * (
                self._params["w"] - 2 * self._params["t"]
            ) ** 3

    def area(self) -> float:
        return self._params["w"] * self._params["h"] - (
            self._params["h"] - 2 * self._params["t"]
        ) * (self._params["w"] - 2 * self._params["t"])

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

        # Deflections
        self.deflections: list[float] = [0.0, 0.0, 0.0]

    def free(self):
        """
        Free translation in all directions

        Returns
        -------
        None
        """
        self.translation_restricted = [False, False, False]

    def pinned(self):
        """
        Restrict translation in all directions, creating a pinned joint

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
    def direction(self) -> NDArray[float]:
        """NDArray[float]: The direction of the member as a unit vector"""
        vector_length = numpy.array(self.end_joint.coordinates) - numpy.array(
            self.begin_joint.coordinates
        )
        return vector_length / numpy.linalg.norm(vector_length)

    @property
    def stiffness(self) -> float:
        """float: The axial stiffness of the member"""
        return self.elastic_modulus * self.area / self.length

    @property
    def stiffness_vector(self) -> NDArray[float]:
        """NDArray[float]: The vector stiffness vector of the member"""
        return self.stiffness * self.direction

    @property
    def stiffness_matrix(self) -> NDArray[float]:
        """NDArray[float]: The local stiffness matrix of the member"""
        d2 = numpy.outer(self.direction, self.direction)
        return self.stiffness * numpy.block([[d2, -d2], [-d2, d2]])

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
