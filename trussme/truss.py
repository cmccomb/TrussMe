import numpy
import pandas
from trussme import joint
from trussme import member
import time
import os


class Truss(object):

    g = 9.81

    def __init__(self):
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

        # Design goals
        self.goals = {"min_fos_total": -1,
                      "min_fos_buckling": -1,
                      "min_fos_yielding": -1,
                      "max_mass": -1,
                      "max_deflection": -1}
        self.THERE_ARE_GOALS = False

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
                raise ValueError(key+' is not an defined design goal. '
                                     'Try min_fos_total, '
                                     'min_fos_yielding, '
                                     'min_fos_buckling, '
                                     'max_mass, or max_deflection.')

    def add_support(self, coordinates, d=3):
        # Make the joint
        self.joints.append(joint.Joint(coordinates))
        self.joints[self.number_of_joints].pinned(d=d)
        self.number_of_joints += 1

    def add_joint(self, coordinates, d=3):
        # Make the joint
        self.joints.append(joint.Joint(coordinates))
        self.joints[self.number_of_joints].free(d=d)
        self.number_of_joints += 1

    def add_member(self, joint_index_a, joint_index_b):
        # Make a member
        self.members.append(member.Member(self.joints[joint_index_a],
                                          self.joints[joint_index_b]))

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
                          - sum([m.mass/2.0*self.g
                                 for m in self.joints[i].members])
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

        forces, deflections, reactions = self.evaluate_forces(truss_info)

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
        self.fos_buckling = min([m.fos_buckling if m.fos_buckling > 0 else 10000 for m in self.members])
        self.fos_yielding = min([m.fos_yielding for m in self.members])

        # Get total FOS and limit state
        self.fos_total = min(self.fos_buckling, self.fos_yielding)
        if self.fos_buckling < self.fos_yielding:
            self.limit_state = 'buckling'
        else:
            self.limit_state = 'yielding'

    def evaluate_forces(self, truss_info):
        Tj = numpy.zeros([3, numpy.size(truss_info["connections"], axis=1)])
        w = numpy.array([numpy.size(truss_info["reactions"], axis=0),
                         numpy.size(truss_info["reactions"], axis=1)])
        SS = numpy.zeros([3*w[1], 3*w[1]])
        deflections = 1.0 - truss_info["reactions"]

        # This identifies joints that can be loaded
        ff = numpy.where(deflections.T.flat == 1)[0]

        # Build the global stiffness matrix
        for i in range(numpy.size(truss_info["connections"], axis=1)):
            H = truss_info["connections"][:, i]
            C = truss_info["coordinates"][:, H[1]] \
                - truss_info["coordinates"][:, H[0]]
            Le = numpy.linalg.norm(C)
            T = C/Le
            s = numpy.outer(T, T)
            G = truss_info["elastic_modulus"][i]*truss_info["area"][i]/Le
            ss = G*numpy.concatenate((numpy.concatenate((s, -s), axis=1),
                                      numpy.concatenate((-s, s), axis=1)),
                                     axis=0)
            Tj[:, i] = G*T
            e = list(range((3*H[0]), (3*H[0] + 3))) \
                + list(range((3*H[1]), (3*H[1] + 3)))
            for ii in range(6):
                for j in range(6):
                    SS[e[ii], e[j]] += ss[ii, j]

        SSff = numpy.zeros([len(ff), len(ff)])
        for i in range(len(ff)):
            for j in range(len(ff)):
                SSff[i, j] = SS[ff[i], ff[j]]

        Loadff = truss_info["loads"].T.flat[ff]
        Uff = numpy.linalg.solve(SSff, Loadff)

        ff = numpy.where(deflections.T == 1)
        for i in range(len(ff[0])):
            deflections[ff[1][i], ff[0][i]] = Uff[i]
        forces = numpy.sum(numpy.multiply(
            Tj, deflections[:, truss_info["connections"][1, :]]
                - deflections[:, truss_info["connections"][0, :]]), axis=0)
        if numpy.linalg.cond(SSff) > pow(10, 10):
            forces *= pow(10, 10)
        reactions = numpy.sum(SS*deflections.T.flat[:], axis=1)\
            .reshape([w[1], w[0]]).T

        return forces, deflections, reactions

    def print_report(self):
        # DO the calcs
        self.calc_mass()
        self.calc_fos()

        print(time.strftime('%X %x %Z'))
        print(os.getcwd())

        self._print_summary()

        self._print_instantiation_information()

        self._print_stress_analysis()

        self._print_recommendations()

    def _print_summary(self):
        print("\n")
        print("(0) SUMMARY OF ANALYSIS")
        print("=============================")
        print("\t- The truss has a mass of " + format(self.mass, '.2f') + " kg, "
              "and a total factor of safety of " + format(self.fos_total, '.2f')
              + ". ")
        print("\t- The limit state is " + self.limit_state + ".")

        if self.THERE_ARE_GOALS:
            success_string = []
            failure_string = []
            for key in self.goals.keys():
                if key is "min_fos_total" and self.goals[key] is not -1:
                    if self.goals[key] < self.fos_total:
                        success_string.append("total FOS")
                    else:
                        failure_string.append("total FOS")
                elif key is "min_fos_buckling" and self.goals[key] is not -1:
                    if self.goals[key] < self.fos_buckling:
                        success_string.append("buckling FOS")
                    else:
                        failure_string.append("buckling FOS")
                elif key is "min_fos_yielding" and self.goals[key] is not -1:
                    if self.goals[key] < self.fos_yielding:
                        success_string.append("yielding FOS")
                    else:
                        failure_string.append("yielding FOS")
                elif key is "max_mass" and self.goals[key] is not -1:
                    if self.goals[key] > self.mass:
                        success_string.append("mass")
                    else:
                        failure_string.append("mass")
                elif key is "max_deflection" and self.goals[key] is not -1:
                    if self.goals[key] > self.fos_total:
                        success_string.append("deflection")
                    else:
                        failure_string.append("deflection")

            if len(success_string) is not 0:
                if len(success_string) is 1:
                    print("\t- The design goal for " + str(success_string[0])
                          + " was satisfied.")
                elif len(success_string) is 2:
                    print("\t- The design goals for " + str(success_string[0])
                          + " and " + str(success_string[1]) + " were satisfied.")
                else:
                    print("\t- The design goals for"),
                    for st in success_string[0:-1]:
                        print(st+","),
                    print("and "+str(success_string[-1])+" were satisfied.")

            if len(failure_string) is not 0:
                if len(failure_string) is 1:
                    print("\t- The design goal for " + str(failure_string[0])
                          + " was not satisfied.")
                elif len(failure_string) is 2:
                    print("- The design goals for " + str(failure_string[0])
                          + " and " + str(failure_string[1]) + " were not satisfied.")
                else:
                    print("The design goals for"),
                    for st in failure_string[0:-1]:
                        print(st+","),
                    print("and "+str(failure_string[-1])+" were not satisfied.")


    def _print_instantiation_information(self):
        print("\n")
        print("(1) INSTANTIATION INFORMATION")
        print("=============================")

        # Print joint information
        print("\n--- JOINTS ---")
        data = []
        rows = []
        for j in self.joints:
            rows.append("Joint_"+str(j.idx))
            data.append([str(j.coordinates[0]),
                         str(j.coordinates[1]),
                         str(j.coordinates[2]),
                         str(bool(j.translation[0][0])),
                         str(bool(j.translation[1][0])),
                         str(bool(j.translation[2][0]))])

        print(pandas.DataFrame(data,
                               index=rows,
                               columns=["X",
                                        "Y",
                                        "Z",
                                        "X-Support",
                                        "Y-Support",
                                        "Z-Support"])
              .to_string(justify="left"))

        # Print member information
        print("\n--- MEMBERS ---")
        data = []
        rows = []
        for m in self.members:
            rows.append("Member_"+str(m.idx))
            data.append([str(m.joints[0].idx),
                         str(m.joints[1].idx),
                         m.material,
                         m.shape,
                         m.h,
                         m.w,
                         m.r,
                         m.t])

        print(pandas.DataFrame(data,
                               index=rows,
                               columns=["Joint-A",
                                        "Joint-B",
                                        "Material",
                                        "Shape",
                                        "Height(m)",
                                        "Width(m)",
                                        "Radius(m)",
                                        "Thickness(m)"])
              .to_string(justify="left"))

        # Print material list
        unique_materials = numpy.unique([m.material for m in self.members])
        print("\n--- MATERIALS ---")
        data = []
        rows = []
        for mat in unique_materials:
            rows.append(mat)
            data.append([
                str(member.Member.materials[mat][0]),
                str(member.Member.materials[mat][1]/pow(10, 9)),
                str(member.Member.materials[mat][2]/pow(10, 6))])

        print(pandas.DataFrame(data,
                               index=rows,
                               columns=["Density(kg/m3)",
                                        "Elastic Modulus(GPa)",
                                        "Yield Strength(MPa)"])
              .to_string(justify="left"))

    def _print_stress_analysis(self):
        print("\n")
        print("(2) STRESS ANALYSIS INFORMATION")
        print("===============================")

        # Print information about loads
        print("\n--- LOADING ---")
        data = []
        rows = []
        for j in self.joints:
            rows.append("Joint_"+str(j.idx))
            data.append([str(j.loads[0][0]/pow(10, 3)),
                         format((j.loads[1][0]
                                 - sum([m.mass/2.0*self.g for m
                                        in j.members]))/pow(10, 3), '.2f'),
                         str(j.loads[2][0]/pow(10, 3))])

        print(pandas.DataFrame(data,
                               index=rows,
                               columns=["X-Load",
                                        "Y-Load",
                                        "Z-Load"])
              .to_string(justify="left"))

        # Print information about reactions
        print("\n--- REACTIONS ---")
        data = []
        rows = []
        for j in self.joints:
            rows.append("Joint_"+str(j.idx))
            data.append([format(j.reactions[0][0]/pow(10, 3), '.2f')
                         if j.translation[0][0] != 0.0 else "N/A",
                         format(j.reactions[1][0]/pow(10, 3), '.2f')
                         if j.translation[1][0] != 0.0 else "N/A",
                         format(j.reactions[2][0]/pow(10, 3), '.2f')
                         if j.translation[2][0] != 0.0 else "N/A"])

        print(pandas.DataFrame(data,
                               index=rows,
                               columns=["X-Reaction(kN)",
                                        "Y-Reaction(kN)",
                                        "Z-Reaction(kN)"])
              .to_string(justify="left"))

        # Print information about members
        print("\n--- FORCES AND STRESSES ---")
        data = []
        rows = []
        for m in self.members:
            rows.append("Member_"+str(m.idx))
            data.append([m.area,
                         format(m.I, '.2e'),
                         format(m.force/pow(10, 3), '.2f'),
                         m.fos_yielding,
                         m.fos_buckling if m.fos_buckling > 0 else "N/A"])

        print(pandas.DataFrame(data,
                               index=rows,
                               columns=["Area(m2)",
                                        "Moment-of-Inertia(m4)",
                                        "Axial-force(kN)",
                                        "FOS-yielding",
                                        "FOS-buckling"])
              .to_string(justify="left"))

        # Print information about members
        print("\n--- DEFLECTIONS ---")
        data = []
        rows = []
        for j in self.joints:
            rows.append("Joint_"+str(j.idx))
            data.append([format(j.deflections[0][0]*pow(10, 3), '.5f')
                         if j.translation[0][0] == 0.0 else "N/A",
                         format(j.deflections[1][0]*pow(10, 3), '.5f')
                         if j.translation[1][0] == 0.0 else "N/A",
                         format(j.deflections[2][0]*pow(10, 3), '.5f')
                         if j.translation[2][0] == 0.0 else "N/A"])

        print(pandas.DataFrame(data,
                               index=rows,
                               columns=["X-Defl.(mm)",
                                        "Y-Defl.(mm)",
                                        "Z-Defl.(mm)"])
              .to_string(justify="left"))

    def _print_recommendations(self):
        MADE_A_RECOMMENDATION = False
        print("\n")
        print("(3) RECOMMENDATIONS")
        print("===============================")
        for m in self.members:
            if self.THERE_ARE_GOALS:
                tyf = self.goals["min_fos_yielding"]
                tbf = self.goals["min_fos_buckling"]
            else:
                tyf = 1.0
                tbf = 1.0
            if m.fos_yielding < tyf:
                print("\t- Member_"+str(m.idx)+": Increase cross-sectional area.")
                MADE_A_RECOMMENDATION = True
            if m.fos_buckling < tbf:
                print("\t- Member_"+str(m.idx)+": Increase moment of inertia.")
                MADE_A_RECOMMENDATION = True

        if not MADE_A_RECOMMENDATION:
            print("No recommendations.")