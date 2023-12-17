import dataclasses
import os
import time
import warnings

import numpy
from numpy.typing import NDArray
from typing import Literal

from trussme import evaluate
from trussme import report
from trussme.components import Joint, Member, g, Material, Pipe, Box, Square, Bar


@dataclasses.dataclass
class Goals:
    min_fos_total: float = 1.0
    min_fos_buckling: float = 1.0
    min_fos_yielding: float = 1.0
    max_mass: float = numpy.inf
    max_deflection: float = numpy.inf


class Truss(object):

    def __init__(self):
        # Make a list to store members in
        self.members: list[Member] = []

        # Make a list to store joints in
        self.joints: list[Joint] = []

        # Design goals
        self.goals: Goals = Goals()

    @property
    def number_of_members(self) -> int:
        return len(self.members)

    @property
    def number_of_joints(self) -> int:
        return len(self.joints)

    @property
    def mass(self) -> float:
        mass = 0
        for m in self.members:
            mass += m.mass
        return mass

    @property
    def fos_yielding(self) -> float:
        return min([m.fos_yielding for m in self.members])

    @property
    def fos_buckling(self) -> float:
        return min([m.fos_buckling if m.fos_buckling > 0 else 10000 for m in self.members])

    @property
    def fos_total(self) -> float:
        return min(self.fos_buckling, self.fos_yielding)

    @property
    def deflection(self) -> float:
        return max([numpy.linalg.norm(joint.deflections) for joint in self.joints])

    @property
    def materials(self) -> list[Material]:
        material_library: list[Material] = [member.material for member in self.members]
        return list({v['name']: v for v in material_library}.values())

    @property
    def limit_state(self) -> str:
        if self.fos_buckling < self.fos_yielding:
            return 'buckling'
        else:
            return 'yielding'

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

    def add_roller_support(self, coordinates: list[float], axis: Literal["x", "y"] = 'y', d: int = 3):
        # Make the joint
        self.joints.append(Joint(coordinates))
        self.joints[-1].roller(axis=axis, d=d)
        self.joints[-1].idx = self.number_of_joints - 1

    def add_joint(self, coordinates: list[float], d: int = 3):
        # Make the joint
        self.joints.append(Joint(coordinates))
        self.joints[-1].free(d=d)
        self.joints[-1].idx = self.number_of_joints - 1

    def add_member(self, joint_index_a: int, joint_index_b: int):
        # Make a member
        self.members.append(Member(self.joints[joint_index_a],
                                   self.joints[joint_index_b]))

        self.members[-1].idx = self.number_of_members - 1

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
            loads[1, i] = self.joints[i].loads[1] - sum([member.mass / 2.0 * g for member in self.joints[i].members])
            loads[2, i] = self.joints[i].loads[2]

        # Pull everything into a dict
        truss_info = {
            "elastic_modulus": numpy.array([member.elastic_modulus for member in self.members]),
            "coordinates": numpy.array([joint.coordinates for joint in self.joints]).T,
            "connections": numpy.array([[member.begin_joint.idx, member.end_joint.idx] for member in self.members]).T,
            "reactions": numpy.array([joint.translation for joint in self.joints]).T,
            "loads": loads,
            "area": numpy.array([member.area for member in self.members])
        }

        forces, deflections, reactions, condition = evaluate.the_forces(truss_info)

        for i in range(self.number_of_members):
            self.members[i].force = forces[i]

        for i in range(self.number_of_joints):
            for j in range(3):
                if self.joints[i].translation[j]:
                    self.joints[i].reactions[j] = reactions[j, i]
                    self.joints[i].deflections[j] = 0.0
                else:
                    self.joints[i].reactions[j] = 0.0
                    self.joints[i].deflections[j] = deflections[j, i]

        if condition > pow(10, 5):
            warnings.warn("The condition number is " + str(condition)
                          + ". Results may be inaccurate.")

    def __report(self, file_name: str = "", verbose: bool = False):

        self.calc_fos()

        if file_name == "":
            f = ""
        else:
            f = open(file_name, 'w')

        # Print date and time
        report.pw(f, time.strftime('%x'), v=verbose)
        report.pw(f, os.getcwd(), v=verbose)

        report.print_summary(f, self, verbose=verbose)

        report.print_instantiation_information(f, self, verbose=verbose)

        report.print_stress_analysis(f, self, verbose=verbose)

        # Try to close, and except if
        if file_name != "":
            f.close()

    def print_and_save_report(self, file_name: str):
        self.__report(file_name=file_name, verbose=True)

    def print_report(self):
        self.__report(file_name="", verbose=True)

    def save_report(self, file_name: str):
        self.__report(file_name=file_name, verbose=False)

    def save_truss(self, file_name: str):

        with open(file_name, "w") as f:
            # Do materials
            for material in self.materials:
                f.write("S" + "\t"
                        + str(material["name"]) + "\t"
                        + str(material["density"]) + "\t"
                        + str(material["elastic_modulus"]) + "\t"
                        + str(material["yield_strength"]) + "\n")

            # Do the joints
            load_string = ""
            for j in self.joints:
                f.write("J" + "\t"
                        + str(j.coordinates[0]) + "\t"
                        + str(j.coordinates[1]) + "\t"
                        + str(j.coordinates[2]) + "\t"
                        + str(int(j.translation[0])) + "\t"
                        + str(int(j.translation[1])) + "\t"
                        + str(int(j.translation[2])) + "\n")
                if numpy.sum(j.loads) != 0:
                    load_string += "L" + "\t"
                    load_string += str(j.idx) + "\t"
                    load_string += str(j.loads[0]) + "\t"
                    load_string += str(j.loads[1]) + "\t"
                    load_string += str(j.loads[2]) + "\t"
                    load_string += "\n"

            # Do the members
            for m in self.members:
                f.write("M" + "\t"
                        + str(m.begin_joint.idx) + "\t"
                        + str(m.end_joint.idx) + "\t"
                        + m.material["name"] + "\t"
                        + m.shape.name() + "\t")
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
    truss = Truss()
    material_library: list[Material] = []

    with open(file_name, 'r') as f:
        for idx, line in enumerate(f):
            if line[0] == "S":
                info = line.split()[1:]
                material_library.append({
                    "name": info[0],
                    "density": float(info[1]),
                    "elastic_modulus": float(info[2]),
                    "yield_strength": float(info[3]),
                })

            elif line[0] == "J":
                info = line.split()[1:]
                truss.add_joint([float(x) for x in info[:3]])
                truss.joints[-1].translation = [bool(int(x)) for x in info[3:]]
            elif line[0] == "M":
                info = line.split()[1:]
                truss.add_member(int(info[0]), int(info[1]))
                material = next(item for item in material_library if item["name"] == info[2])
                truss.members[-1].set_material(material)

                # Parse parameters
                ks = []
                vs = []
                for param in range(4, len(info)):
                    kvpair = info[param].split("=")
                    ks.append(kvpair[0])
                    vs.append(float(kvpair[1]))
                shape = eval(str(info[3]).title())(**dict(zip(ks, vs)))
                truss.members[-1].set_shape(shape)

            elif line[0] == "L":
                info = line.split()[1:]
                truss.joints[int(info[0])].loads[0] = float(info[1])
                truss.joints[int(info[0])].loads[1] = float(info[2])
                truss.joints[int(info[0])].loads[2] = float(info[3])
            elif line[0] != "#" and not line.isspace():
                raise ValueError("'" + line[0] + "' is not a valid line initializer.")

    return truss
