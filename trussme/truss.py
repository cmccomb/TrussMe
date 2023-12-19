import dataclasses
import warnings
from typing import Literal
import json

import numpy

from trussme import evaluate
from trussme import report
from trussme.components import (
    Joint,
    Member,
    g,
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
    min_fos_total: float, default=1.0
        Minimum total FOS for the truss, defaults to 1.0
    min_fos_buckling: float, default=1.0
        Minimum buckling FOS for the truss, defaults to 1.0
    min_fos_yielding: float, default=1.0
        Minimum yielding FOS for the truss, defaults to 1.0
    max_mass: float, default=inf
        Maximum mass for the truss, defaults to inf
    max_deflection: float, default=inf
        Maximum deflection for the truss, defaults to inf

    """

    min_fos_total: float = 1.0
    min_fos_buckling: float = 1.0
    min_fos_yielding: float = 1.0
    max_mass: float = numpy.inf
    max_deflection: float = numpy.inf


class Truss(object):
    """The truss class

    Attributes
    ----------
    number_of_members
    number_of_joints
    mass
    fos_yielding
    fos_buckling
    fos_total
    deflection
    """

    def __init__(self):
        # Make a list to store members in
        self.members: list[Member] = []

        # Make a list to store joints in
        self.joints: list[Joint] = []

        # Design goals
        self.goals: Goals = Goals()

    @property
    def number_of_members(self) -> int:
        """Number of members in the truss, updated automatically

        Returns
        -------
        int
        """
        return len(self.members)

    @property
    def number_of_joints(self) -> int:
        """Number of joints in the truss, updated automatically

        Returns
        -------
        int
        """
        return len(self.joints)

    @property
    def mass(self) -> float:
        """Total mass of the truss, updated automatically

        Returns
        -------
        float
        """
        mass = 0
        for m in self.members:
            mass += m.mass
        return mass

    @property
    def fos_yielding(self) -> float:
        """Smallest yielding FOS in the truss

        Returns
        -------
        float
        """
        return min([m.fos_yielding for m in self.members])

    @property
    def fos_buckling(self) -> float:
        """Smallest buckling FOS in the truss

        Returns
        -------
        float
        """
        return min(
            [m.fos_buckling if m.fos_buckling > 0 else 10000 for m in self.members]
        )

    @property
    def fos_total(self) -> float:
        """Smallest FOS in the truss

        Returns
        -------
        float
        """
        return min(self.fos_buckling, self.fos_yielding)

    @property
    def deflection(self) -> float:
        """Largest single joint deflection in the truss

        Returns
        -------
        float
        """
        return max([numpy.linalg.norm(joint.deflections) for joint in self.joints])

    @property
    def materials(self) -> list[Material]:
        """List of unique materials used in the truss

        Returns
        -------
        list[Material]
        """
        material_library: list[Material] = [member.material for member in self.members]
        return list({v["name"]: v for v in material_library}.values())

    @property
    def limit_state(self) -> Literal["buckling", "yielding"]:
        """The limit state of the truss, either "buckling" or "yielding"

        Returns
        -------
        Literal["buckling", "yielding"]
        """
        if self.fos_buckling < self.fos_yielding:
            return "buckling"
        else:
            return "yielding"

    @property
    def minimum_fos_total(self) -> float:
        return self.goals.min_fos_total

    @minimum_fos_total.setter
    def minimum_fos_total(self, new_fos: float):
        self.goals.min_fos_total = new_fos

    @property
    def minimum_fos_yielding(self) -> float:
        return self.goals.min_fos_yielding

    @minimum_fos_yielding.setter
    def minimum_fos_yielding(self, new_fos: float):
        self.goals.min_fos_yielding = new_fos

    @property
    def minimum_fos_buckling(self) -> float:
        return self.goals.min_fos_buckling

    @minimum_fos_buckling.setter
    def minimum_fos_buckling(self, new_fos: float):
        self.goals.min_fos_buckling = new_fos

    @property
    def maximum_mass(self) -> float:
        return self.goals.max_mass

    @maximum_mass.setter
    def maximum_mass(self, new_mass: float):
        self.goals.max_mass = new_mass

    @property
    def maximum_deflection(self) -> float:
        return self.goals.max_deflection

    @maximum_deflection.setter
    def maximum_deflection(self, new_deflection: float):
        self.goals.max_deflection = new_deflection

    def add_pinned_support(self, coordinates: list[float]):
        # Make the joint
        self.joints.append(Joint(coordinates))
        self.joints[-1].pinned()
        self.joints[-1].idx = self.number_of_joints - 1

    def add_roller_support(
        self, coordinates: list[float], axis: Literal["x", "y"] = "y", d: int = 3
    ):
        # Make the joint
        self.joints.append(Joint(coordinates))
        self.joints[-1].roller(axis=axis, d=d)
        self.joints[-1].idx = self.number_of_joints - 1

    def add_joint(self, coordinates: list[float], d: int = 3):
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
        self.joints[joint_index].coordinates = coordinates

    def set_load(self, joint_index: int, load: list[float]):
        self.joints[joint_index].loads = load

    def calc_fos(self):
        loads = numpy.zeros([3, self.number_of_joints])
        for i in range(self.number_of_joints):
            loads[0, i] = self.joints[i].loads[0]
            loads[1, i] = self.joints[i].loads[1] - sum(
                [member.mass / 2.0 * g for member in self.joints[i].members]
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

        if condition > pow(10, 5):
            warnings.warn(
                "The condition number is "
                + str(condition)
                + ". Results may be inaccurate."
            )

    @property
    def report(self) -> str:
        """
        :return: A string containing a full report on the truss
        :rtype: str
        """
        self.calc_fos()

        report_string = report.generate_summary(self) + "\n"
        report_string += report.generate_instantiation_information(self) + "\n"
        report_string += report.generate_stress_analysis(self) + "\n"

        return report_string

    def report_to_md(self, file_name: str) -> None:
        """
        Writes a report in Markdown format
        :param file_name: A string with the name of the file
        :type file_name: str
        :return: None
        """
        with open(file_name, "w") as f:
            f.write(self.report)

    def to_json(self, file_name: str) -> None:
        """
        Saves the truss to a JSON file
        :param file_name: The filename to use for the truss file
        :type file_name: str
        :return: None
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
        :param file_name: The filename to use for the truss file
        :type file_name: str
        :return: None
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
    :param file_name: The name of the .trs file to be read
    :type file_name: str
    :return: The object loaded from the .trs file
    :rtype: Truss
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
    :param file_name: The name of the JSON file to be read
    :type file_name: str
    :return: The object loaded from the JSON file
    :rtype: Truss
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
