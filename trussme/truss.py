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

        # Design goals
        self.fos_total = -1
        self.fos_buckling = -1
        self.fos_total = -1
        self.fos_total = -1
        
    def make_random_truss(self, xlim=[-10, 10], ylim=[-10, 10]):
        # Draw joints
        # Determine which joints should be supports
        # Add members
        # Evaluate
        asdf = 1

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
        # self.fos_buckling =

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
        print(time.strftime('%X %x %Z'))
        print(os.getcwd())

        # Print Section header
        print("\n")
        print("(1) INSTANTIATION INFORMATION")
        print("=============================")

        # Print joint information
        print("\n--- JOINTS ---")
        data = []
        rows = []
        for j in self.joints:
            temp = []
            rows.append(j.idx)
            temp.append(str(j.coordinates[0]))
            temp.append(str(j.coordinates[1]))
            temp.append(str(j.coordinates[2]))
            temp.append(str(bool(j.translation[0][0])))
            temp.append(str(bool(j.translation[1][0])))
            temp.append(str(bool(j.translation[2][0])))
            data.append(temp)

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
            temp = []
            rows.append(str(m.idx))
            temp.append(str(m.joints[0].idx))
            temp.append(str(m.joints[1].idx))
            temp.append(m.material)
            temp.append(m.shape)
            temp.append(m.h)
            temp.append(m.w)
            temp.append(m.r)
            temp.append(m.t)
            data.append(temp)

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
        for mat in unique_materials:
            data.append([
                mat,
                str(member.Member.materials[mat][0]),
                str(member.Member.materials[mat][1]/pow(10, 9)),
                str(member.Member.materials[mat][2]/pow(10, 6))])

        print(pandas.DataFrame(data,
                               columns=["Material",
                                        "Density(kg/m3)",
                                        "Elastic Modulus(GPa)",
                                        "Yield Strength(MPa)"])
              .to_string(justify="left"))

        print("\n")
        print("(2) STRESS ANALYSIS INFORMATION")
        print("===============================")

        # Print information about loads
        print("\n--- LOADING ---")
        data = []
        rows = []
        for j in self.joints:
            temp = []
            rows.append(j.idx)
            temp.append(str(j.loads[0][0]/pow(10, 3)))
            temp.append(format((j.loads[1][0]
                                - sum([m.mass/2.0*self.g
                                       for m in j.members]))/pow(10, 3), '.2f'))
            temp.append(str(j.loads[2][0]/pow(10, 3)))
            data.append(temp)

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
            temp = []
            rows.append(j.idx)
            temp.append(format(j.reactions[0][0]/pow(10, 3), '.2f')
                        if j.translation[0][0] != 0.0 else "N/A")
            temp.append(format(j.reactions[1][0]/pow(10, 3), '.2f')
                        if j.translation[1][0] != 0.0 else "N/A")
            temp.append(format(j.reactions[2][0]/pow(10, 3), '.2f')
                        if j.translation[2][0] != 0.0 else "N/A")
            data.append(temp)

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
            temp = []
            rows.append(m.idx)
            temp.append(m.area)
            temp.append(format(m.I, '.2e'))
            temp.append(format(m.force/pow(10, 3), '.2f'))
            temp.append(m.fos_yield)
            temp.append(m.fos_buckling)
            data.append(temp)

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
            temp = []
            rows.append(j.idx)
            temp.append(format(j.deflections[0][0]*pow(10, 3), '.5f')
                        if j.translation[0][0] == 0.0 else "N/A")
            temp.append(format(j.deflections[1][0]*pow(10, 3), '.5f')
                        if j.translation[1][0] == 0.0 else "N/A")
            temp.append(format(j.deflections[2][0]*pow(10, 3), '.5f')
                        if j.translation[2][0] == 0.0 else "N/A")
            data.append(temp)

        print(pandas.DataFrame(data,
                               index=rows,
                               columns=["X-Defl.(mm)",
                                        "Y-Defl.(mm)",
                                        "Z-Defl.(mm)"])
              .to_string(justify="left"))

        print("\n")
        print("(3) RECOMMENDATIONS")
        print("===============================")
        print("\nlorem ipsum")
