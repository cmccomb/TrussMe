import numpy
from trussme import joint
from trussme import member
from trussme import report
from trussme import evaluate
from trussme.physical_properties import g
import time
import os
import warnings


class Truss(object):

    def __init__(self, file_name=""):
        # Make a list to store members in
        self.members = []

        # Make a list to store joints in
        self.joints = []

        # Variables to store number of joints and members
        self.number_of_joints = 0
        self.number_of_members = 0

        # Variables to store truss characteristics
        self.mass = 0
        self.fos_yielding = 0
        self.fos_buckling = 0
        self.fos_total = 0
        self.limit_state = ''
        self.condition = 0

        # Design goals
        self.goals = {"min_fos_total": -1,
                      "min_fos_buckling": -1,
                      "min_fos_yielding": -1,
                      "max_mass": -1,
                      "max_deflection": -1}
        self.THERE_ARE_GOALS = False

        if file_name is not "":
            with open(file_name, 'r') as f:
                for idx, line in enumerate(f):
                    if line[0] is "J":
                        info = line.split()[1:]
                        self.add_joint(numpy.array(
                            [float(x) for x in info[:3]]))
                        self.joints[-1].translation = numpy.array(
                            [[int(x)] for x in info[3:]])
                    elif line[0] is "M":
                        info = line.split()[1:]
                        self.add_member(int(info[0]), int(info[1]))
                        self.members[-1].set_material(info[2])
                        self.members[-1].set_shape(info[3])

                        # Parse parameters
                        ks = []
                        vs = []
                        for param in range(4, len(info)):
                            kvpair = info[param].split("=")
                            ks.append(kvpair[0])
                            vs.append(float(kvpair[1]))
                        self.members[-1].set_parameters(**dict(zip(ks, vs)))
                    elif line[0] is "L":
                        info = line.split()[1:]
                        self.joints[int(info[0])].loads[0] = float(info[1])
                        self.joints[int(info[0])].loads[1] = float(info[2])
                        self.joints[int(info[0])].loads[2] = float(info[3])
                    elif line[0] is not "#" and not line.isspace():
                        raise ValueError("'"+line[0] +
                                         "' is not a valid line beginner.")

    def set_goal(self, **kwargs):
        self.THERE_ARE_GOALS = True
        for key in kwargs:
            if key is "min_fos_total":
                self.goals["min_fos_total"] = kwargs["min_fos_total"]
            elif key is "min_fos_yielding":
                self.goals["min_fos_yielding"] = kwargs["min_fos_yielding"]
            elif key is "min_fos_buckling":
                self.goals["min_fos_buckling"] = kwargs["min_fos_buckling"]
            elif key is "max_mass":
                self.goals["max_mass"] = kwargs["max_mass"]
            elif key is "max_deflection":
                self.goals["max_deflection"] = kwargs["max_deflection"]
            else:
                self.THERE_ARE_GOALS = False
                raise ValueError(key+' is not a valid defined design goal. '
                                     'Try min_fos_total, '
                                     'min_fos_yielding, '
                                     'min_fos_buckling, '
                                     'max_mass, or max_deflection.')

    def add_support(self, coordinates, d=3):
        # Make the joint
        self.joints.append(joint.Joint(coordinates))
        self.joints[self.number_of_joints].pinned(d=d)
        self.joints[-1].idx = self.number_of_joints
        self.number_of_joints += 1

    def add_joint(self, coordinates, d=3):
        # Make the joint
        self.joints.append(joint.Joint(coordinates))
        self.joints[self.number_of_joints].free(d=d)
        self.joints[-1].idx = self.number_of_joints
        self.number_of_joints += 1

    def add_member(self, joint_index_a, joint_index_b):
        # Make a member
        self.members.append(member.Member(self.joints[joint_index_a],
                                          self.joints[joint_index_b]))

        self.members[-1].idx = self.number_of_members

        # Update joints
        self.joints[joint_index_a].members.append(self.members[-1])
        self.joints[joint_index_b].members.append(self.members[-1])

        self.number_of_members += 1

    def move_joint(self, joint_index, coordinates):
        self.joints[joint_index].coordinates = coordinates

    def calc_mass(self):
        self.mass = 0
        for m in self.members:
            self.mass += m.mass

    def set_load(self, joint_index, load):
        self.joints[joint_index].load = load

    def calc_fos(self):
        # Pull supports and add to D
        coordinates = []
        for j in self.joints:
            coordinates.append(j.coordinates)

        # Build Re
        reactions = numpy.zeros([3, self.number_of_joints])
        loads = numpy.zeros([3, self.number_of_joints])
        for i in range(len(self.joints)):
            reactions[0, i] = self.joints[i].translation[0]
            reactions[1, i] = self.joints[i].translation[1]
            reactions[2, i] = self.joints[i].translation[2]
            loads[0, i] = self.joints[i].loads[0]
            loads[1, i] = self.joints[i].loads[1]\
                - sum([m.mass/2.0*g for m in self.joints[i].members])
            loads[2, i] = self.joints[i].loads[2]

        # Pull out E and A
        elastic_modulus = []
        area = []
        connections = []
        for m in self.members:
            elastic_modulus.append(m.elastic_modulus)
            area.append(m.area)
            connections.append([j.idx for j in m.joints])

        # Make everything an array
        area = numpy.array(area)
        elastic_modulus = numpy.array(elastic_modulus)
        coordinates = numpy.array(coordinates).T
        connections = numpy.array(connections).T

        # Pull everything into a dict
        truss_info = {"elastic_modulus": elastic_modulus,
                      "coordinates": coordinates,
                      "connections": connections,
                      "reactions": reactions,
                      "loads": loads,
                      "area": area}

        forces, deflections, reactions, self.condition = \
            evaluate.the_forces(truss_info)

        for i in range(self.number_of_members):
            self.members[i].set_force(forces[i])

        for i in range(self.number_of_joints):
            for j in range(3):
                if self.joints[i].translation[j]:
                    self.joints[i].reactions[j] = reactions[j, i]
                    self.joints[i].deflections[j] = 0.0
                else:
                    self.joints[i].reactions[j] = 0.0
                    self.joints[i].deflections[j] = deflections[j, i]

        # Pull out the member factors of safety
        self.fos_buckling = min([m.fos_buckling if m.fos_buckling > 0
                                 else 10000 for m in self.members])
        self.fos_yielding = min([m.fos_yielding for m in self.members])

        # Get total FOS and limit state
        self.fos_total = min(self.fos_buckling, self.fos_yielding)
        if self.fos_buckling < self.fos_yielding:
            self.limit_state = 'buckling'
        else:
            self.limit_state = 'yielding'

        if self.condition > pow(10, 5):
            warnings.warn("The condition number is " + str(self.condition)
                          + ". Results may be inaccurate.")

    def __report(self, file_name="", verb=False):

        # DO the calcs
        self.calc_mass()
        self.calc_fos()

        if file_name is "":
            f = ""
        else:
            f = open(file_name, 'w')

        # Print date and time
        report.pw(f, time.strftime('%X %x %Z'), v=verb)
        report.pw(f, os.getcwd(), v=verb)

        report.print_summary(f, self, verb=verb)

        report.print_instantiation_information(f, self, verb=verb)

        report.print_stress_analysis(f, self, verb=verb)

        if self.THERE_ARE_GOALS:
            report.print_recommendations(f, self, verb=verb)

        # Try to close, and except if
        if file_name is not "":
            f.close()

    def print_and_save_report(self, file_name):
        self.__report(file_name=file_name, verb=True)

    def print_report(self):
        self.__report(file_name="", verb=True)

    def save_report(self, file_name):
        self.__report(file_name=file_name, verb=False)

    def save_truss(self, file_name=""):
        if file_name is "":
            file_name = time.strftime('%X %x %Z')

        with open(file_name, "w") as f:
            # Do the joints
            load_string = ""
            for j in self.joints:
                f.write("J" + "\t"
                        + str(j.coordinates[0]) + "\t"
                        + str(j.coordinates[1]) + "\t"
                        + str(j.coordinates[2]) + "\t"
                        + str(j.translation[0, 0]) + "\t"
                        + str(j.translation[1, 0]) + "\t"
                        + str(j.translation[2, 0]) + "\n")
                if numpy.sum(j.loads) != 0:
                    load_string += "L" + "\t"
                    load_string += str(j.idx) + "\t"
                    load_string += str(j.loads[0, 0]) + "\t"
                    load_string += str(j.loads[1, 0]) + "\t"
                    load_string += str(j.loads[2, 0]) + "\t"
                    load_string += "\n"

            # Do the members
            for m in self.members:
                f.write("M" + "\t"
                        + str(m.joints[0].idx) + "\t"
                        + str(m.joints[1].idx) + "\t"
                        + m.material + "\t"
                        + m.shape + "\t")
                if m.t != "N/A":
                    f.write("t=" + str(m.t) + "\t")
                if m.r != "N/A":
                    f.write("r=" + str(m.r) + "\t")
                if m.w != "N/A":
                    f.write("w=" + str(m.w) + "\t")
                if m.h != "N/A":
                    f.write("h=" + str(m.h) + "\t")
                f.write("\n")

            # Do the loads
            f.write(load_string)