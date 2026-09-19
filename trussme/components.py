import abc
from dataclasses import dataclass
from typing import TypedDict, Literal, cast

import numpy
from numpy.typing import NDArray

Material = TypedDict(
    "Material",
    {
        "name": str,
        "density": float,
        "elastic_modulus": float,
        "yield_strength": float,
        "source": str,
    },
)
"""TypedDict: New type to contain material properties.

The ``source`` field stores a URL pointing to the origin of the
mechanical property data for traceability.
"""

MATERIAL_LIBRARY: list[Material] = [
    {
        "name": "A36_Steel",
        "density": 7850.0,
        "elastic_modulus": 200 * pow(10, 9),
        "yield_strength": 250 * pow(10, 6),
        "source": "https://en.wikipedia.org/wiki/A36_steel",
    },
    {
        "name": "A992_Steel",
        "density": 7850.0,
        "elastic_modulus": 200 * pow(10, 9),
        "yield_strength": 345 * pow(10, 6),
        "source": "https://en.wikipedia.org/wiki/ASTM_A992",
    },
    {
        "name": "6061_T6_Aluminum",
        "density": 2700.0,
        "elastic_modulus": 68.9 * pow(10, 9),
        "yield_strength": 276 * pow(10, 6),
        "source": "https://en.wikipedia.org/wiki/6061_aluminium_alloy",
    },
    {
        "name": "7075_T6_Aluminum",
        "density": 2810.0,
        "elastic_modulus": 71.7 * pow(10, 9),
        "yield_strength": 503 * pow(10, 6),
        "source": "https://en.wikipedia.org/wiki/7075_aluminium_alloy",
    },
    {
        "name": "2024_T3_Aluminum",
        "density": 2780.0,
        "elastic_modulus": 73.1 * pow(10, 9),
        "yield_strength": 324 * pow(10, 6),
        "source": "https://en.wikipedia.org/wiki/2024_aluminium_alloy",
    },
    {
        "name": "304_Stainless_Steel",
        "density": 8000.0,
        "elastic_modulus": 193 * pow(10, 9),
        "yield_strength": 215 * pow(10, 6),
        "source": "https://en.wikipedia.org/wiki/SAE_304_stainless_steel",
    },
    {
        "name": "Ti_6Al_4V_Titanium",
        "density": 4430.0,
        "elastic_modulus": 113.8 * pow(10, 9),
        "yield_strength": 880 * pow(10, 6),
        "source": "https://en.wikipedia.org/wiki/Ti-6Al-4V",
    },
]
"""list[Material]: List of built-in materials to choose from
"""


class Shape(abc.ABC):
    """
    Abstract base class for shapes, useful for typehints and creating new shapes

    Examples
    --------
    >>> import trussme
    >>> class MagicalRod(trussme.Shape):
    ...     def __init__(self):
    ...         self._params = {}
    ...
    ...     def moi(self) -> float:
    ...         return 200_000_000_000
    ...
    ...     def area(self) -> float:
    ...         return 100_000
    ...
    ...     def name(self) -> str:
    ...         return "magical rod"
    ...
    >>> magical_rod = MagicalRod()
    >>> magical_rod.moi()
    200000000000
    >>> magical_rod.area()
    100000
    >>> magical_rod.name()
    'magical rod'
    """

    @abc.abstractmethod
    def __init__(self):
        self._params = {}

    @abc.abstractmethod
    def moi(self) -> float:
        """
        Legacy scalar inertia (larger principal inertia for rectangles).
        Use principal_inertias() for directional buckling checks.

        Returns
        -------
        float
            The moment of inertia of the shape
        """
        pass

    def principal_inertias(self) -> tuple[float, float]:
        """Inertias for the two transverse deflection directions.

        Legacy subclasses with only ``moi`` are treated as isotropic. Override
        this method for an asymmetric section. Rectangles return height first.
        """
        return (self.moi(), self.moi())

    def validate(self) -> None:
        """Reject nonphysical section properties before structural analysis."""
        values = [self.area(), *self.principal_inertias()]
        if not all(numpy.isfinite(v) and v > 0 for v in values):
            raise ValueError(
                "Section area and principal inertias must be finite and positive"
            )
        if self.name() in ("pipe", "bar", "square", "box", "custom") and not all(
            numpy.isfinite(v) and v > 0 for v in self._params.values()
        ):
            raise ValueError("Section dimensions must be finite and positive")
        p = self._params
        if self.name() == "pipe" and p["t"] > p["r"]:
            raise ValueError("Pipe thickness must not exceed its radius")
        if self.name() == "box" and 2 * p["t"] > min(p["w"], p["h"]):
            raise ValueError("Box thickness must not exceed half its smaller dimension")

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

    Examples
    --------
    >>> import trussme
    >>> pipe = trussme.Pipe(r=1.0, t=1.0)
    >>> round(pipe.moi(), 3)
    0.785
    >>> round(pipe.area(), 3)
    3.142
    """

    def __init__(self, r: float, t: float):
        self._params = {"r": r, "t": t}

    def moi(self) -> float:
        return (numpy.pi / 4.0) * (
            self._params["r"] ** 4 - (self._params["r"] - self._params["t"]) ** 4
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

    Examples
    --------
    >>> import trussme
    >>> bar = trussme.Bar(r=1.0)
    >>> round(bar.moi(), 3)
    0.785
    >>> round(bar.area(), 3)
    3.142
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

    Examples
    --------
    >>> import trussme
    >>> square = trussme.Square(w=1.0, h=1.0)
    >>> round(square.moi(), 3)
    0.083
    >>> square.area()
    1.0
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

    def principal_inertias(self) -> tuple[float, float]:
        w, h = self._params["w"], self._params["h"]
        return (w * h**3 / 12, h * w**3 / 12)

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

    Examples
    --------
    >>> import trussme
    >>> box = trussme.Box(w=1.0, h=1.0, t=0.5)
    >>> round(box.moi(), 3)
    0.083
    >>> box.area()
    1.0
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

    def principal_inertias(self) -> tuple[float, float]:
        w, h, t = self._params["w"], self._params["h"], self._params["t"]
        return (
            (w * h**3 - (w - 2 * t) * (h - 2 * t) ** 3) / 12,
            (h * w**3 - (h - 2 * t) * (w - 2 * t) ** 3) / 12,
        )


class Custom(Shape):
    """Section defined by area and two principal inertias in SI units."""

    def __init__(self, area: float, i1: float, i2: float):
        self._params = {"area": area, "i1": i1, "i2": i2}

    def area(self) -> float:
        return self._params["area"]

    def moi(self) -> float:
        return max(self.principal_inertias())

    def principal_inertias(self) -> tuple[float, float]:
        return (self._params["i1"], self._params["i2"])

    def name(self) -> str:
        return "custom"


@dataclass(frozen=True)
class BucklingSettings:
    """Section orientation and caller-supplied effective length factors.

    The projected reference is the first deflection direction; the second is
    member direction crossed with the first. K factors do not add physical braces.
    """

    transverse_reference: tuple[float, float, float] | None = None
    effective_length_factors: tuple[float, float] = (1.0, 1.0)

    def __post_init__(self):
        factors = tuple(self.effective_length_factors)
        if len(factors) != 2 or not all(numpy.isfinite(k) and k > 0 for k in factors):
            raise ValueError(
                "Two finite positive effective length factors are required"
            )
        object.__setattr__(self, "effective_length_factors", factors)
        if self.transverse_reference is not None:
            ref = tuple(self.transverse_reference)
            if len(ref) != 3 or not all(numpy.isfinite(v) for v in ref) or not any(ref):
                raise ValueError(
                    "Transverse reference must be a finite nonzero 3-vector"
                )
            object.__setattr__(self, "transverse_reference", ref)


@dataclass(frozen=True)
class BucklingMode:
    """Euler member capacity check, not a geometric-stiffness eigenmode."""

    direction: tuple[float, float, float]
    moment_of_inertia: float
    effective_length: float
    critical_load: float
    factor_of_safety: float


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
        self.buckling = BucklingSettings()
        self.buckling_axis: Literal["weak", "strong"] = "weak"

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
        return float(
            numpy.linalg.norm(
                numpy.array(self.begin_joint.coordinates)
                - numpy.array(self.end_joint.coordinates)
            )
        )

    @property
    def direction(self) -> NDArray[numpy.float64]:
        """NDArray[numpy.float64]: The direction of the member as a unit vector"""
        vector_length: NDArray[numpy.float64] = numpy.array(
            self.end_joint.coordinates
        ) - numpy.array(self.begin_joint.coordinates)
        magnitude = float(numpy.linalg.norm(vector_length))
        if magnitude == 0.0:
            return numpy.zeros_like(vector_length, dtype=numpy.float64)
        return cast(NDArray[numpy.float64], vector_length / magnitude)

    @property
    def stiffness(self) -> float:
        """float: The axial stiffness of the member"""
        length = self.length
        if length == 0.0:
            raise ValueError("Member length must be greater than zero")
        return self.elastic_modulus * self.area / length

    @property
    def stiffness_vector(self) -> NDArray[numpy.float64]:
        """NDArray[numpy.float64]: The vector stiffness vector of the member"""
        return numpy.multiply(self.stiffness, self.direction)

    @property
    def stiffness_matrix(self) -> NDArray[numpy.float64]:
        """NDArray[numpy.float64]: The local stiffness matrix of the member"""
        d2: NDArray[numpy.float64] = cast(
            NDArray[numpy.float64], numpy.outer(self.direction, self.direction)
        )
        block = numpy.block([[d2, -d2], [-d2, d2]]).astype(numpy.float64)
        return cast(NDArray[numpy.float64], numpy.multiply(self.stiffness, block))

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
        if not numpy.isfinite(new_force):
            raise ValueError("Member force must be finite")
        self._force = new_force

    @property
    def fos_yielding(self) -> float:
        """float: The factor of safety against yielding"""
        applied_force = abs(self.force)
        if applied_force == 0.0:
            return numpy.inf
        return self.yield_strength * abs(self.area) / applied_force

    @property
    def fos_buckling(self) -> float:
        """Scalar safety; weak governs by default, strong is legacy compatibility."""
        modes = self.buckling_modes
        select = min if self.buckling_axis == "weak" else max
        return select(m.factor_of_safety for m in modes)

    @property
    def buckling_modes(self) -> tuple[BucklingMode, BucklingMode]:
        """Both transverse Euler capacities and global deflection directions."""
        self.shape.validate()
        length = self.length
        if not numpy.isfinite(length) or length <= 0:
            raise ValueError("Member length must be greater than zero and finite")
        if not numpy.isfinite(self.elastic_modulus) or self.elastic_modulus <= 0:
            raise ValueError("Elastic modulus must be finite and positive")
        axis = self.direction
        reference = self.buckling.transverse_reference
        ref = (
            numpy.eye(3)[numpy.argmin(numpy.abs(axis))]
            if reference is None
            else numpy.array(reference, dtype=float)
        )
        ref = ref / numpy.max(numpy.abs(ref))
        first = ref - numpy.dot(ref, axis) * axis
        norm = numpy.linalg.norm(first)
        if norm <= 1e-12:
            raise ValueError("Transverse reference must not be parallel to the member")
        first /= norm
        second = numpy.cross(axis, first)
        modes = []
        for direction, inertia, k in zip(
            (first, second),
            self.shape.principal_inertias(),
            self.buckling.effective_length_factors,
        ):
            effective = k * length
            critical = numpy.pi**2 * self.elastic_modulus * inertia / effective**2
            if not numpy.isfinite(critical) or critical <= 0:
                raise ValueError("Euler critical load must be finite and positive")
            modes.append(
                BucklingMode(
                    tuple(float(v) for v in direction),
                    inertia,
                    effective,
                    critical,
                    critical / -self.force if self.force < 0 else numpy.inf,
                )
            )
        return (modes[0], modes[1])

    @property
    def governing_buckling(self) -> BucklingMode:
        """Lower capacity mode, independent of the legacy scalar convention.

        Equal capacities have no unique governing direction; the first is returned.
        """
        return min(self.buckling_modes, key=lambda mode: mode.critical_load)
