import dataclasses
from typing import Literal, Union
import json

import numpy
from numpy.typing import NDArray
import scipy

from trussme.components import (
    Joint,
    Member,
    Material,
    Pipe,
    Bar,
    Square,
    Shape,
    Box,
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


class Truss(object):
    """The truss class

    Attributes
    ----------
    members: list[Member]
        A list of all members in the truss
    joints: list[Joint]
        A list of all joints in the truss
    """

    def __init__(self):
        # Make a list to store members in
        self.members: list[Member] = []

        # Make a list to store joints in
        self.joints: list[Joint] = []

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
        return max([numpy.linalg.norm(joint.deflections) for joint in self.joints])

    @property
    def materials(self) -> list[Material]:
        """list[Material]: List of unique materials used in the truss"""
        material_library: list[Material] = [member.material for member in self.members]
        return list({v["name"]: v for v in material_library}.values())

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

    def add_out_of_plane_support(self, constrained_axis: Literal["x", "y", "z"] = "z"):
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
    ):
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
        """

        member = Member(
            self.joints[begin_joint_index],
            self.joints[end_joint_index],
            material,
            shape,
        )
        member.idx = self.number_of_members

        # Make a member
        self.members.append(member)

        # Update joints
        self.joints[begin_joint_index].members.append(self.members[-1])
        self.joints[end_joint_index].members.append(self.members[-1])

    def move_joint(self, joint_index: int, coordinates: list[float]):
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

    def set_load(self, joint_index: int, load: list[float]):
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
        loads = numpy.zeros([3, self.number_of_joints])
        for i in range(self.number_of_joints):
            loads[0, i] = self.joints[i].loads[0]
            loads[1, i] = self.joints[i].loads[1] - sum(
                [
                    member.mass / 2.0 * scipy.constants.g
                    for member in self.joints[i].members
                ]
            )
            loads[2, i] = self.joints[i].loads[2]

        return loads

    @property
    def __connection_matrix(self) -> NDArray[float]:
        return numpy.array(
            [[member.begin_joint.idx, member.end_joint.idx] for member in self.members]
        ).T

    def analyze(self):
        """
        Analyze the truss

        Returns
        -------
        None

        """
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

        ff = numpy.where(deflections.T == 1)
        for i in range(len(ff[0])):
            deflections[ff[1][i], ff[0][i]] = flat_deflections[i]

        # Compute the reactions
        reactions = (
            numpy.sum(dof * deflections.T.flat[:], axis=1)
            .reshape([self.number_of_joints, 3])
            .T
        )

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
        }

        if file_name is None:
            return json.dumps(combined)
        else:
            with open(file_name, "w") as f:
                json.dump(combined, f, indent=4)

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
                if numpy.sum(j.loads) != 0:
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

    with open(file_name, "r") as f:
        for idx, line in enumerate(f):
            if line[0] == "S":
                info = line.split()[1:]
                material_library.append(
                    {
                        "name": info[0],
                        "density": float(info[1]),
                        "elastic_modulus": float(info[2]),
                        "yield_strength": float(info[3]),
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
                truss.add_member(int(info[0]), int(info[1]), material, shape)

            elif line[0] == "L":
                info = line.split()[1:]
                truss.joints[int(info[0])].loads[0] = float(info[1])
                truss.joints[int(info[0])].loads[1] = float(info[2])
                truss.joints[int(info[0])].loads[2] = float(info[3])
            elif line[0] != "#" and not line.isspace():
                raise ValueError("'" + line[0] + "' is not a valid line initializer.")

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
        else:
            raise ValueError(
                "Shape type '"
                + member["shape"]["name"]
                + "' is a custom type and not supported."
            )
        truss.add_member(
            member["begin_joint"], member["end_joint"], material=material, shape=shape
        )

    return truss
