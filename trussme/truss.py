import dataclasses
from typing import Literal, Union
import json

import numpy
from numpy.typing import NDArray

from trussme.components import (
    Joint,
    Member,
    Material,
    Pipe,
    Bar,
    Square,
    Shape,
    Box,
    Custom,
    BucklingSettings,
    MATERIAL_LIBRARY,
)


@dataclasses.dataclass
class Goals:
    """Container of goals for truss design.

    Attributes
    ----------
    minimum_fos_buckling: float, default=1.0
        Minimum buckling FOS for the truss, defaults to 1.0
    minimum_fos_yielding: float, default=1.0
        Minimum yielding FOS for the truss, defaults to 1.0
    maximum_mass: float, default=inf
        Maximum mass for the truss, defaults to inf
    maximum_deflection: float, default=inf
        Maximum deflection for the truss, defaults to inf

    Examples
    --------
    This is a goal container with the default values
    >>> import trussme
    >>> import numpy
    >>> goals = trussme.Goals(
    ...    minimum_fos_buckling=1.0,
    ...    minimum_fos_yielding=1.0,
    ...    maximum_mass=numpy.inf,
    ...    maximum_deflection=numpy.inf,
    ... )
    """

    minimum_fos_buckling: float = 1.0
    minimum_fos_yielding: float = 1.0
    maximum_mass: float = numpy.inf
    maximum_deflection: float = numpy.inf

    def validate(self) -> None:
        for value in (self.minimum_fos_buckling, self.minimum_fos_yielding):
            if not numpy.isfinite(value) or value < 0:
                raise ValueError(
                    "Minimum safety factors must be finite and nonnegative"
                )
        for value in (self.maximum_mass, self.maximum_deflection):
            if numpy.isnan(value) or value < 0:
                raise ValueError("Maximum mass and deflection must be nonnegative")

    def evaluate(self, truss: "Truss") -> list[float]:
        """Four dimensionless residuals, feasible at <= 0, on an analyzed truss.

        Order: governing directional buckling, yielding, deflection, mass.
        Infinite upper limits are disabled (-1). Both buckling modes are always
        checked, including when the model uses the legacy strong scalar setting.
        """
        self.validate()

        def upper(actual, limit):
            return -1.0 if numpy.isinf(limit) else (actual - limit) / max(limit, 1.0)

        return [
            self.minimum_fos_buckling / truss.fos_buckling_governing - 1,
            self.minimum_fos_yielding / truss.fos_yielding - 1,
            upper(truss.deflection, self.maximum_deflection),
            upper(truss.mass, self.maximum_mass),
        ]


class Truss(object):
    """The truss class

    Attributes
    ----------
    members: list[Member]
        A list of all members in the truss
    joints: list[Joint]
        A list of all joints in the truss
    """

    def __init__(
        self,
        gravity=(0.0, -9.80665, 0.0),
        buckling_axis: Literal["weak", "strong"] = "weak",
    ):
        # Make a list to store members in
        self.members: list[Member] = []

        # Make a list to store joints in
        self.joints: list[Joint] = []
        self.set_gravity(gravity)
        self.set_buckling_axis(buckling_axis)

    @property
    def gravity(self) -> tuple[float, float, float]:
        """Acceleration in m/s²; zero disables self-weight."""
        return self._gravity

    def set_gravity(self, gravity) -> None:
        values = tuple(float(v) for v in gravity)
        if len(values) != 3 or not all(numpy.isfinite(v) for v in values):
            raise ValueError("Gravity must be a finite 3-vector")
        self._gravity = values

    @property
    def buckling_axis(self) -> str:
        return self._buckling_axis

    def set_buckling_axis(self, axis: Literal["weak", "strong"]) -> None:
        if axis not in ("weak", "strong"):
            raise ValueError("Buckling axis must be 'weak' or 'strong'")
        self._buckling_axis = axis
        for member in self.members:
            member.buckling_axis = axis

    def set_member_buckling(
        self, member_index: int, settings: BucklingSettings
    ) -> None:
        member = self.members[member_index]
        previous = member.buckling
        member.buckling = settings
        try:
            _ = member.buckling_modes
        except (ValueError, TypeError, AttributeError):
            member.buckling = previous
            raise

    @property
    def fos_buckling_governing(self) -> float:
        """Smallest safety across both modes of every member."""
        return min(m.governing_buckling.factor_of_safety for m in self.members)

    @property
    def nodal_loads(self) -> NDArray[numpy.float64]:
        """N-by-3 applied loads plus half each member's weight at each endpoint."""
        loads = numpy.array([j.loads for j in self.joints], dtype=float).reshape(
            (-1, 3)
        )
        for member in self.members:
            weight = member.mass * numpy.array(self.gravity) / 2
            loads[member.begin_joint.idx] += weight
            loads[member.end_joint.idx] += weight
        return loads

    def _metadata(self) -> dict:
        return {
            "gravity": self.gravity,
            "buckling_axis": self.buckling_axis.title(),
            "member_buckling": [dataclasses.asdict(m.buckling) for m in self.members],
        }

    def _read_metadata(self, settings: dict) -> None:
        # An explicit extension is never silently ignored or partially applied.
        if set(settings) != {"gravity", "buckling_axis", "member_buckling"}:
            raise ValueError("Unsupported or incomplete trussx metadata")
        if settings["buckling_axis"] not in ("Weak", "Strong"):
            raise ValueError("Unsupported buckling axis in metadata")
        if len(settings["member_buckling"]) != self.number_of_members:
            raise ValueError("Buckling settings must match the member count")
        self.set_gravity(settings["gravity"])
        self.set_buckling_axis(settings["buckling_axis"].lower())
        for member, record in zip(self.members, settings["member_buckling"]):
            if "effective_length_factors" not in record:
                raise ValueError(
                    "Member metadata must specify effective length factors"
                )
            member.buckling = BucklingSettings(**record)
            # Default settings also support zero-size optimizer templates. Explicit
            # orientation must be checked against actual member geometry now.
            if member.buckling.transverse_reference is not None:
                _ = member.buckling_modes

    def validate(self) -> None:
        """Validate mechanical inputs before analysis; model objects remain mutable."""
        if not self.joints or not self.members:
            raise ValueError("Analysis requires joints and members")
        for joint in self.joints:
            for values in (joint.coordinates, joint.loads):
                if len(values) != 3 or not all(numpy.isfinite(v) for v in values):
                    raise ValueError(
                        "Joint coordinates and loads must be finite 3-vectors"
                    )
            if len(joint.translation_restricted) != 3:
                raise ValueError("Joint restrictions must have three components")
        for member in self.members:
            member.shape.validate()
            for key in ("density", "elastic_modulus", "yield_strength"):
                if (
                    not numpy.isfinite(member.material[key])
                    or member.material[key] <= 0
                ):
                    raise ValueError("Material properties must be finite and positive")
            _ = member.buckling_modes

    @property
    def number_of_members(self) -> int:
        """int: Number of members in the truss"""
        return len(self.members)

    @property
    def number_of_joints(self) -> int:
        """int: Number of joints in the truss"""
        return len(self.joints)

    @property
    def mass(self) -> float:
        """float: Total mass of the truss"""
        mass = 0
        for m in self.members:
            mass += m.mass
        return mass

    @property
    def fos_yielding(self) -> float:
        """float: Smallest yielding FOS of any member in the truss"""
        return min([m.fos_yielding for m in self.members])

    @property
    def fos_buckling(self) -> float:
        """float: Smallest buckling FOS of any member in the truss"""
        return min([m.fos_buckling for m in self.members])

    @property
    def fos(self) -> float:
        """float: Smallest FOS of any member in the truss"""
        return min(self.fos_buckling, self.fos_yielding)

    @property
    def deflection(self) -> float:
        """float: Largest single joint deflection in the truss"""
        return float(
            max([numpy.linalg.norm(joint.deflections) for joint in self.joints])
        )

    @property
    def materials(self) -> list[Material]:
        """list[Material]: List of unique materials used in the truss"""
        library = {}
        for member in self.members:
            material = member.material
            if material["name"] in library and library[material["name"]] != material:
                raise ValueError("Conflicting material name: " + material["name"])
            library[material["name"]] = material
        return list(library.values())

    @property
    def limit_state(self) -> Literal["buckling", "yielding"]:
        """Literal["buckling", "yielding"]: The limit state of the truss, either "buckling" or "yielding" """
        if self.fos_buckling < self.fos_yielding:
            return "buckling"
        else:
            return "yielding"

    def is_planar(self) -> Literal["x", "y", "z", "none"]:
        """
        Check if the truss is planar

        Returns
        -------
        Literal["x", "y", "z", "none"]
            The axis along which the truss is planar, or None if it is not planar
        """

        restriction = numpy.prod(
            numpy.array([joint.translation_restricted for joint in self.joints]),
            axis=0,
        )

        # Check if the truss is planar
        if (restriction == [False, False, False]).all():
            return "none"
        elif (restriction == [True, False, False]).all():
            return "x"
        elif (restriction == [False, True, False]).all():
            return "y"
        elif (restriction == [False, False, True]).all():
            return "z"
        else:
            return "none"

    def add_pinned_joint(self, coordinates: list[float]) -> int:
        """Add a pinned joint to the truss at the given coordinates

        Parameters
        ----------
        coordinates: list[float]
            The coordinates of the joint

        Returns
        -------
        int:
            The index of the new joint
        """

        # Make the joint
        self.joints.append(Joint(coordinates))
        self.joints[-1].pinned()
        self.joints[-1].idx = self.number_of_joints - 1

        return self.joints[-1].idx

    def add_roller_joint(
        self, coordinates: list[float], constrained_axis: Literal["x", "y", "z"] = "y"
    ) -> int:
        """
        Add a roller joint to the truss at the given coordinates

        Parameters
        ----------
        coordinates: list[float]
            The coordinates of the joint
        constrained_axis: Literal["x", "y", "z"], default="y"
            The axis along which the joint is not allowed to translate

        Returns
        -------
        int:
            The index of the new joint
        """

        self.joints.append(Joint(coordinates))
        self.joints[-1].roller(constrained_axis=constrained_axis)
        self.joints[-1].idx = self.number_of_joints - 1

        return self.joints[-1].idx

    def add_slotted_joint(
        self, coordinates: list[float], free_axis: Literal["x", "y", "z"] = "y"
    ) -> int:
        """
        Add a slotted joint to the truss at the given coordinates

        Parameters
        ----------
        coordinates: list[float]
            The coordinates of the joint
        free_axis: Literal["x", "y", "z"], default="y"
            The axis along which the joint is allowed to translate

        Returns
        -------
        int:
            The index of the new joint
        """

        self.joints.append(Joint(coordinates))
        self.joints[-1].slot(free_axis=free_axis)
        self.joints[-1].idx = self.number_of_joints - 1

        return self.joints[-1].idx

    def add_free_joint(self, coordinates: list[float]) -> int:
        """
        Add a free joint to the truss at the given coordinates

        Parameters
        ----------
        coordinates: list[float]
            The coordinates of the joint

        Returns
        -------
        int:
            The index of the new joint
        """

        # Make the joint
        self.joints.append(Joint(coordinates))
        self.joints[-1].free()
        self.joints[-1].idx = self.number_of_joints - 1

        return self.joints[-1].idx

    def add_out_of_plane_support(
        self, constrained_axis: Literal["x", "y", "z"] = "z"
    ) -> None:
        for idx in range(self.number_of_joints):
            if constrained_axis == "x":
                self.joints[idx].translation_restricted[0] = True
            elif constrained_axis == "y":
                self.joints[idx].translation_restricted[1] = True
            elif constrained_axis == "z":
                self.joints[idx].translation_restricted[2] = True

    def add_member(
        self,
        begin_joint_index: int,
        end_joint_index: int,
        material: Material = MATERIAL_LIBRARY[0],
        shape: Shape = Pipe(t=0.002, r=0.02),
    ) -> int:
        """
        Add a member to the truss

        Parameters
        ----------
        begin_joint_index: int
            The index of the first joint
        end_joint_index: int
            The index of the second joint
        material: Material, default=material_library[0]
            The material of the member
        shape: Shape, default=Pipe(t=0.002, r=0.02)
            The shape of the member

        Returns
        -------
        int
            The index of the new member

        Raises
        ------
        IndexError
            If ``begin_joint_index`` or ``end_joint_index`` are out of range.
        ValueError
            If ``begin_joint_index`` and ``end_joint_index`` refer to the same joint.
        """
        if not 0 <= begin_joint_index < self.number_of_joints:
            msg = f"begin_joint_index {begin_joint_index} is out of range"
            raise IndexError(msg)
        if not 0 <= end_joint_index < self.number_of_joints:
            msg = f"end_joint_index {end_joint_index} is out of range"
            raise IndexError(msg)
        if begin_joint_index == end_joint_index:
            raise ValueError("begin_joint_index and end_joint_index must differ")

        member = Member(
            self.joints[begin_joint_index],
            self.joints[end_joint_index],
            material,
            shape,
        )
        member.idx = self.number_of_members
        member.buckling_axis = self.buckling_axis

        # Make a member
        self.members.append(member)

        # Update joints
        self.joints[begin_joint_index].members.append(self.members[-1])
        self.joints[end_joint_index].members.append(self.members[-1])

        return member.idx

    def move_joint(self, joint_index: int, coordinates: list[float]) -> None:
        """
        Move a joint to the given coordinates

        Parameters
        ----------
        joint_index: int
            The index of the joint to move
        coordinates: list[float]
            The coordinates to move the joint to

        Returns
        -------
        None
        """
        self.joints[joint_index].coordinates = coordinates

    def set_load(self, joint_index: int, load: list[float]) -> None:
        """Apply loads to a given joint
        Parameters
        ----------
        joint_index: int
            The index of the joint to apply the load to
        load: list[float]
            The load to apply to the joint
        Returns
        -------
        None
        """

        self.joints[joint_index].loads = load

    @property
    def __load_matrix(self) -> NDArray[float]:
        return self.nodal_loads.T

    @property
    def __connection_matrix(self) -> NDArray[float]:
        return numpy.array(
            [[member.begin_joint.idx, member.end_joint.idx] for member in self.members]
        ).T

    def analyze(self) -> None:
        """
        Analyze the truss

        Returns
        -------
        None

        """
        self.validate()
        loads = self.__load_matrix
        connections = self.__connection_matrix
        reactions = numpy.array(
            [joint.translation_restricted for joint in self.joints]
        ).T

        tj: NDArray[float] = numpy.zeros([3, self.number_of_members])
        dof: NDArray[float] = numpy.zeros(
            [3 * self.number_of_joints, 3 * self.number_of_joints]
        )
        deflections: NDArray[float] = numpy.ones([3, self.number_of_joints])
        deflections -= reactions

        # This identifies joints that can be loaded
        ff: NDArray[float] = numpy.where(deflections.T.flat == 1)[0]

        for idx, member in enumerate(self.members):
            ss = member.stiffness_matrix
            tj[:, idx] = member.stiffness_vector

            e = list(
                range((3 * member.begin_joint.idx), (3 * member.begin_joint.idx + 3))
            ) + list(range((3 * member.end_joint.idx), (3 * member.end_joint.idx + 3)))
            for ii in range(6):
                for j in range(6):
                    dof[e[ii], e[j]] += ss[ii, j]

        ssff = numpy.zeros([len(ff), len(ff)])
        for i in range(len(ff)):
            for j in range(len(ff)):
                ssff[i, j] = dof[ff[i], ff[j]]

        flat_loads = loads.T.flat[ff]
        flat_deflections = numpy.linalg.solve(ssff, flat_loads)
        if not numpy.isfinite(flat_deflections).all():
            raise ValueError("Analysis produced nonfinite displacements")

        ff = numpy.where(deflections.T == 1)
        for i in range(len(ff[0])):
            deflections[ff[1][i], ff[0][i]] = flat_deflections[i]

        # Compute the reactions
        reactions = (
            numpy.sum(dof * deflections.T.flat[:], axis=1)
            .reshape([self.number_of_joints, 3])
            .T
        ) - loads

        # Store the results
        for i in range(self.number_of_joints):
            for j in range(3):
                if self.joints[i].translation_restricted[j]:
                    self.joints[i].reactions[j] = float(reactions[j, i])
                    self.joints[i].deflections[j] = 0.0
                else:
                    self.joints[i].reactions[j] = 0.0
                    self.joints[i].deflections[j] = float(deflections[j, i])

        # Calculate member forces and store the results
        forces = numpy.sum(
            numpy.multiply(
                tj,
                deflections[:, connections[1, :]] - deflections[:, connections[0, :]],
            ),
            axis=0,
        )
        # Store the results
        for i in range(self.number_of_members):
            self.members[i].force = forces[i]

        return None

    def to_json(self, file_name: Union[None, str] = None) -> Union[str, None]:
        """
        Saves the truss to a JSON file

        Parameters
        ----------
        file_name: Union[None, str]
            The filename to use for the JSON file. If None, the json is returned as a string

        Returns
        -------
        Union[str, None]
        """

        class JointEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, Joint):
                    return {
                        "coordinates": obj.coordinates,
                        "loads": obj.loads,
                        "translation": obj.translation_restricted,
                    }
                # Let the base class default method raise the TypeError
                return json.JSONEncoder.default(self, obj)

        class MemberEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, Member):
                    return {
                        "begin_joint": obj.begin_joint.idx,
                        "end_joint": obj.end_joint.idx,
                        "material": obj.material["name"],
                        "shape": {
                            "name": obj.shape.name(),
                            "parameters": obj.shape._params,
                        },
                    }
                # Let the base class default method raise the TypeError
                return json.JSONEncoder.default(self, obj)

        materials = json.dumps(self.materials, indent=4)
        joints = json.dumps(self.joints, indent=4, cls=JointEncoder)
        members = json.dumps(self.members, indent=4, cls=MemberEncoder)

        combined = {
            "materials": json.loads(materials),
            "joints": json.loads(joints),
            "members": json.loads(members),
            "trussx": self._metadata(),
        }

        if file_name is None:
            return json.dumps(combined, allow_nan=False)
        else:
            with open(file_name, "w") as f:
                json.dump(combined, f, indent=4, allow_nan=False)
            return None

    def to_trs(self, file_name: str) -> None:
        """
        Saves the truss to a .trs file

        Parameters
        ----------
        file_name: str
            The filename to use for the truss file

        Returns
        -------
        None
        """

        with open(file_name, "w") as f:
            f.write("# trussx " + json.dumps(self._metadata(), allow_nan=False) + "\n")
            # Do materials
            for material in self.materials:
                f.write(
                    "S"
                    + "\t"
                    + str(material["name"])
                    + "\t"
                    + str(material["density"])
                    + "\t"
                    + str(material["elastic_modulus"])
                    + "\t"
                    + str(material["yield_strength"])
                    + "\t"
                    + material["source"]
                    + "\n"
                )

            # Do the joints
            load_string = ""
            for j in self.joints:
                f.write(
                    "J"
                    + "\t"
                    + str(j.coordinates[0])
                    + "\t"
                    + str(j.coordinates[1])
                    + "\t"
                    + str(j.coordinates[2])
                    + "\t"
                    + str(int(j.translation_restricted[0]))
                    + "\t"
                    + str(int(j.translation_restricted[1]))
                    + "\t"
                    + str(int(j.translation_restricted[2]))
                    + "\n"
                )
                if any(value != 0 for value in j.loads):
                    load_string += "L" + "\t"
                    load_string += str(j.idx) + "\t"
                    load_string += str(j.loads[0]) + "\t"
                    load_string += str(j.loads[1]) + "\t"
                    load_string += str(j.loads[2]) + "\t"
                    load_string += "\n"

            # Do the members
            for m in self.members:
                f.write(
                    "M"
                    + "\t"
                    + str(m.begin_joint.idx)
                    + "\t"
                    + str(m.end_joint.idx)
                    + "\t"
                    + m.material["name"]
                    + "\t"
                    + m.shape.name()
                    + "\t"
                )
                for key in m.shape._params.keys():
                    f.write(key + "=" + str(m.shape._params[key]) + "\t")
                f.write("\n")

            # Do the loads
            f.write(load_string)


def read_trs(file_name: str) -> Truss:
    """
    Read a .trs file and return a Truss object

    Parameters
    ----------
    file_name: str
        The name of the .trs file to be read

    Returns
    -------
    Truss
        The object loaded from the .trs file
    """
    truss = Truss()
    material_library: list[Material] = []
    metadata = None

    with open(file_name, "r") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            if line.startswith("# trussx "):
                if metadata is not None:
                    raise ValueError("Duplicate trussx metadata")
                metadata = json.loads(line[len("# trussx ") :])
                continue
            if line[0] == "S":
                info = line.split()[1:]
                material_library.append(
                    {
                        "name": info[0],
                        "density": float(info[1]),
                        "elastic_modulus": float(info[2]),
                        "yield_strength": float(info[3]),
                        "source": info[4] if len(info) > 4 else "",
                    }
                )

            elif line[0] == "J":
                info = line.split()[1:]
                truss.add_free_joint([float(x) for x in info[:3]])
                truss.joints[-1].translation_restricted = [
                    bool(int(x)) for x in info[3:]
                ]
            elif line[0] == "M":
                info = line.split()[1:]
                material = next(
                    item for item in material_library if item["name"] == info[2]
                )

                # Parse parameters
                ks = []
                vs = []
                for param in range(4, len(info)):
                    kvpair = info[param].split("=")
                    ks.append(kvpair[0])
                    vs.append(float(kvpair[1]))
                if info[3] == "pipe":
                    shape = Pipe(**dict(zip(ks, vs)))
                elif info[3] == "bar":
                    shape = Bar(**dict(zip(ks, vs)))
                elif info[3] == "square":
                    shape = Square(**dict(zip(ks, vs)))
                elif info[3] == "box":
                    shape = Box(**dict(zip(ks, vs)))
                elif info[3] == "custom":
                    shape = Custom(**dict(zip(ks, vs)))
                else:
                    raise ValueError("Unsupported shape: " + info[3])
                truss.add_member(int(info[0]), int(info[1]), material, shape)

            elif line[0] == "L":
                info = line.split()[1:]
                truss.joints[int(info[0])].loads[0] = float(info[1])
                truss.joints[int(info[0])].loads[1] = float(info[2])
                truss.joints[int(info[0])].loads[2] = float(info[3])
            elif line[0] != "#" and not line.isspace():
                raise ValueError("'" + line[0] + "' is not a valid line initializer.")

    if metadata is not None:
        truss._read_metadata(metadata)
    return truss


def read_json(file_name: str) -> Truss:
    """
    Read a JSON file and return a Truss object

    Parameters
    ----------
    file_name: str
        The name of the JSON file to be read, or a valid JSON string

    Returns
    -------
    Truss
        The object loaded from the JSON file
    """
    try:
        json_truss = json.loads(file_name)
    except ValueError:
        with open(file_name, "r") as file:
            json_truss = json.load(file)

    truss = Truss()
    current_material_library: list[Material] = json_truss["materials"]

    for joint in json_truss["joints"]:
        truss.add_free_joint(joint["coordinates"])
        truss.joints[-1].translation_restricted = joint["translation"]
        truss.joints[-1].loads = joint["loads"]

    for member in json_truss["members"]:
        material: Material = next(
            item
            for item in current_material_library
            if item["name"] == member["material"]
        )
        shape_params = member["shape"]["parameters"]
        if member["shape"]["name"] == "pipe":
            shape = Pipe(**dict(shape_params))
        elif member["shape"]["name"] == "bar":
            shape = Bar(**dict(shape_params))
        elif member["shape"]["name"] == "square":
            shape = Square(**dict(shape_params))
        elif member["shape"]["name"] == "box":
            shape = Box(**dict(shape_params))
        elif member["shape"]["name"] == "custom":
            shape = Custom(**dict(shape_params))
        else:
            raise ValueError(
                "Shape type '"
                + member["shape"]["name"]
                + "' is a custom type and not supported."
            )
        truss.add_member(
            member["begin_joint"], member["end_joint"], material=material, shape=shape
        )

    if "trussx" in json_truss:
        truss._read_metadata(json_truss["trussx"])
    return truss
