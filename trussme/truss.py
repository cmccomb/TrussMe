import dataclasses
from typing import Literal
import json

import numpy
import scipy

from trussme import evaluate
from trussme import report
from trussme.components import (
    Joint,
    Member,
    Material,
    Pipe,
    Bar,
    Square,
    Shape,
    Box,
    material_library,
)


@dataclasses.dataclass
class Goals:
    """Container of goals for truss design.

    Attributes
    ----------
    minimum_fos_total: float, default=1.0
        Minimum total FOS for the truss, defaults to 1.0
    minimum_fos_buckling: float, default=1.0
        Minimum buckling FOS for the truss, defaults to 1.0
    minimum_fos_yielding: float, default=1.0
        Minimum yielding FOS for the truss, defaults to 1.0
    maximum_mass: float, default=inf
        Maximum mass for the truss, defaults to inf
    maximum_deflection: float, default=inf
        Maximum deflection for the truss, defaults to inf
    """

    minimum_fos_total: float = 1.0
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
        return min(
            [m.fos_buckling if m.fos_buckling > 0 else 10000 for m in self.members]
        )

    @property
    def fos_total(self) -> float:
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

    def add_pinned_support(self, coordinates: list[float]):
        """Add a pinned support to the truss at the given coordinates

        Parameters
        ----------
        coordinates: list[float]
            The coordinates of the joint

        Returns
        -------
        None
        """

        # Make the joint
        self.joints.append(Joint(coordinates))
        self.joints[-1].pinned()
        self.joints[-1].idx = self.number_of_joints - 1

    def add_roller_support(
        self, coordinates: list[float], axis: Literal["x", "y"] = "y", d: int = 3
    ):
        """
        Add a roller support to the truss at the given coordinates

        Parameters
        ----------
        coordinates: list[float]
            The coordinates of the joint
        axis: Literal["x", "y"], default="y"
            The axis of the roller support TODO: Fix this
        d: int, default=3
            The number of degrees of freedom to constrain TODO: Fix this

        Returns
        -------
        None
        """

        # Make the joint
        self.joints.append(Joint(coordinates))
        self.joints[-1].roller(axis=axis, d=d)
        self.joints[-1].idx = self.number_of_joints - 1

    def add_joint(self, coordinates: list[float], d: int = 3):
        """
        Add a free joint to the truss at the given coordinates

        Parameters
        ----------
        coordinates: list[float]
            The coordinates of the joint
        d: int, default=3
            The number of degrees of freedom to constrain TODO: Fix this

        Returns
        -------
        None
        """

        # Make the joint
        self.joints.append(Joint(coordinates))
        self.joints[-1].free(d=d)
        self.joints[-1].idx = self.number_of_joints - 1

    def add_member(
        self,
        joint_index_a: int,
        joint_index_b: int,
        material: Material = material_library[0],
        shape: Shape = Pipe(t=0.002, r=0.02),
    ):
        """
        Add a member to the truss

        Parameters
        ----------
        joint_index_a: int
            The index of the first joint
        joint_index_b: int
            The index of the second joint
        material: Material, default=material_library[0]
            The material of the member
        shape: Shape, default=Pipe(t=0.002, r=0.02)
            The shape of the member

        Returns
        -------
        None
        """

        member = Member(
            self.joints[joint_index_a], self.joints[joint_index_b], material, shape
        )
        member.idx = self.number_of_members

        # Make a member
        self.members.append(member)

        # Update joints
        self.joints[joint_index_a].members.append(self.members[-1])
        self.joints[joint_index_b].members.append(self.members[-1])

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

    def calc_fos(self):
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

        # Pull everything into a dict
        truss_info = {
            "elastic_modulus": numpy.array(
                [member.elastic_modulus for member in self.members]
            ),
            "coordinates": numpy.array([joint.coordinates for joint in self.joints]).T,
            "connections": numpy.array(
                [
                    [member.begin_joint.idx, member.end_joint.idx]
                    for member in self.members
                ]
            ).T,
            "reactions": numpy.array([joint.translation for joint in self.joints]).T,
            "loads": loads,
            "area": numpy.array([member.area for member in self.members]),
        }

        forces, deflections, reactions, condition = evaluate.the_forces(truss_info)

        for i in range(self.number_of_members):
            self.members[i].force = forces[i]

        for i in range(self.number_of_joints):
            for j in range(3):
                if self.joints[i].translation[j]:
                    self.joints[i].reactions[j] = float(reactions[j, i])
                    self.joints[i].deflections[j] = 0.0
                else:
                    self.joints[i].reactions[j] = 0.0
                    self.joints[i].deflections[j] = float(deflections[j, i])

    def report(self, goals: Goals) -> str:
        """
        Generates a report on the truss

        Parameters
        ----------
        goals: Goals
            The goals against which to evaluate the truss

        Returns
        -------
        str
            A full report on the truss
        """
        self.calc_fos()

        report_string = report.generate_summary(self, goals) + "\n"
        report_string += report.generate_instantiation_information(self) + "\n"
        report_string += report.generate_stress_analysis(self, goals) + "\n"

        return report_string

    def report_to_md(self, file_name: str, goals: Goals) -> None:
        """
        Writes a report in Markdown format

        Parameters
        ----------
        file_name: str
            The name of the file
        goals: Goals
            The goals against which to evaluate the truss

        Returns
        -------
        None
        """
        with open(file_name, "w") as f:
            f.write(self.report(goals))

    def to_json(self, file_name: str) -> None:
        """
        Saves the truss to a JSON file

        Parameters
        ----------
        file_name: str
            The filename to use for the JSON file

        Returns
        -------
        None
        """

        class JointEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, Joint):
                    return {
                        "coordinates": obj.coordinates,
                        "loads": obj.loads,
                        "translation": obj.translation,
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
                            "w": obj.shape.w,
                            "h": obj.shape.h,
                            "r": obj.shape.r,
                            "t": obj.shape.t,
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
                    + str(int(j.translation[0]))
                    + "\t"
                    + str(int(j.translation[1]))
                    + "\t"
                    + str(int(j.translation[2]))
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
                if m.shape.t:
                    f.write("t=" + str(m.shape.t) + "\t")
                if m.shape.r:
                    f.write("r=" + str(m.shape.r) + "\t")
                if m.shape.w:
                    f.write("w=" + str(m.shape.w) + "\t")
                if m.shape.h:
                    f.write("h=" + str(m.shape.h) + "\t")
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
                truss.add_joint([float(x) for x in info[:3]])
                truss.joints[-1].translation = [bool(int(x)) for x in info[3:]]
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
        The name of the JSON file to be read

    Returns
    -------
    Truss
        The object loaded from the JSON file
    """
    json_truss = json.load(open(file_name))

    truss = Truss()
    material_library: list[Material] = json_truss["materials"]

    for joint in json_truss["joints"]:
        truss.add_joint(joint["coordinates"])
        truss.joints[-1].translation = joint["translation"]
        truss.joints[-1].translation = joint["loads"]

    for member in json_truss["members"]:
        material: Material = next(
            item for item in material_library if item["name"] == member["material"]
        )
        shape_params = member["shape"]
        del shape_params["name"]
        if member["shape"]["name"] == "pipe":
            shape = Pipe(**dict(shape_params))
        elif member["shape"]["name"] == "bar":
            shape = Bar(**dict(shape_params))
        elif member["shape"]["name"] == "square":
            shape = Square(**dict(shape_params))
        elif member["shape"]["name"] == "box":
            shape = Box(**dict(shape_params))
        truss.add_member(
            member["begin_joint"], member["end_joint"], material=material, shape=shape
        )

    return truss
