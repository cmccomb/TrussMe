import numpy
import pandas
from trussme import joint
from trussme import member
import time
import os

class Truss(object):

    def __init__(self):
        # Make a list to store members in
        self.members = []

        # Make a list to store joints in
        self.joints = []

        # Variables to store number of joints and members
        self.n = 0
        self.m = 0

        # Variables to store truss characteristics
        self.mass = 0
        self.fos_yielding = 0
        self.fos_buckling = 0
        self.fos_total = 0
        
    def make_random_truss(self, xlim=[-10, 10], ylim=[-10, 10]):
        # Draw joints
        # Determine which joints should be supportrs
        # Add members
        # Evaluate
        asdf = 1

    def add_support(self, coordinates, d=3):
        # Make the joint
        self.joints.append(joint.Joint(coordinates))
        self.joints[self.n].pinned(d=d)
        self.n += 1

    def add_joint(self, coordinates, d=3):
        # Make the joint
        self.joints.append(joint.Joint(coordinates))
        self.joints[self.n].free(d=d)
        self.n += 1

    def add_member(self, j1, j2):
        # Make a member
        self.members.append(member.Member(self.joints[j1], self.joints[j2]))

        # Update joints
        self.joints[j1].members.append(self.members[-1])
        self.joints[j2].members.append(self.members[-1])

        self.m += 1

    def move_joint(self, j, coordinates):
        self.joints[j].coordinates = coordinates

    def calc_mass(self):
        self.mass = 0
        for m in self.members:
            self.mass += m.mass

    def calc_fos(self):
        D = {}

        # Pull supports and add to D
        D["Re"] = []
        for j in self.joints:
            D["Re"].append(j.translation)

        # Pull out E and A
        D["E"] = []
        D["A"] = []
        for m in self.members:
            D["E"].append(m.E)
            D["A"].append(m.A)

        # PUll out

    def force_eval(self, D):
        Tj = numpy.zeros([3, numpy.size(D["Con"], axis=1)])
        w = numpy.array([numpy.size(D["Re"], axis=0), numpy.size(D["Re"], axis=1)])
        SS = numpy.zeros([3*w[1], 3*w[1]])
        U = 1.0 - D["Re"]

        # This identifies joints that are unsupported, and can therefore be loaded
        ff = numpy.where(U.T.flat == 1)[0]

        # Step through the each member in the truss, and build the global stiffness matrix
        for i in range(numpy.size(D["Con"], axis=1)):
            H = D["Con"][:, i]
            C = D["Coord"][:, H[1]] - D["Coord"][:, H[0]]
            Le = numpy.linalg.norm(C)
            T = C/Le
            s = numpy.outer(T, T)
            G = D["E"][i]*D["A"][i]/Le
            ss = G*numpy.concatenate((numpy.concatenate((s, -s), axis=1), numpy.concatenate((-s, s), axis=1)), axis=0)
            Tj[:, i] = G*T
            e = range((3*H[0]), (3*H[0] + 3)) + range((3*H[1]), (3*H[1] + 3))
            for ii in range(6):
                for j in range(6):
                    SS[e[ii], e[j]] += ss[ii, j]

        SSff = numpy.zeros([len(ff), len(ff)])
        for i in range(len(ff)):
            for j in range(len(ff)):
                SSff[i,j] = SS[ff[i], ff[j]]

        Loadff = D["Load"].T.flat[ff]
        Uff = numpy.linalg.solve(SSff, Loadff)

        ff = numpy.where(U.T==1)
        for i in range(len(ff[0])):
            U[ff[1][i], ff[0][i]] = Uff[i]
        F = numpy.sum(numpy.multiply(Tj, U[:, D["Con"][1,:]] - U[:, D["Con"][0,:]]), axis=0)
        if numpy.linalg.cond(SSff) > pow(10,10):
            F *= pow(10, 10)
        R = numpy.sum(SS*U.T.flat[:], axis=1).reshape([w[1], w[0]]).T

        return F, U, R

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
            temp.append(str(j.translation[0][0]))
            temp.append(str(j.translation[1][0]))
            temp.append(str(j.translation[2][0]))
            data.append(temp)

        print(pandas.DataFrame(data,
                               index=rows,
                               columns=["X",
                                        "Y",
                                        "Z",
                                        "X-Trans",
                                        "Y-Trans",
                                        "Z-Trans"])
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
                               columns=["Joint A",
                                        "Joint B",
                                        "Material",
                                        "Shape",
                                        "Height (m)",
                                        "Width (m)",
                                        "Radius (m)",
                                        "Thickness (m)"])
              .to_string(justify="left"))

        # Print material list
        unique_materials = numpy.unique([m.material for m in self.members])
        print("\n--- MATERIALS ---")
        data = []
        for mat in unique_materials:
            temp = []
            temp.append(mat)
            temp.append(str(member.Member.materials[mat][0]))
            temp.append(str(member.Member.materials[mat][1]/pow(10, 9)))
            temp.append(str(member.Member.materials[mat][2]/pow(10, 6)))
            data.append(temp)

        print(pandas.DataFrame(data,
                               columns=["Material",
                                        "Density (kg/m3)",
                                        "Elastic Modulus (GPa)",
                                        "Yield Strength (Pa)"])
              .to_string(justify="left"))

        print("\n")
        print("(2) STRESS ANALYSIS INFORMATION")
        print("===============================")
        print("\nlorem ipsum")

        print("\n")
        print("(3) DEFLECTION ANALYSIS INFORMATION")
        print("===============================")
        print("\nlorem ipsum")

        print("\n")
        print("(4) RECOMMENDATIONS")
        print("===============================")
        print("\nlorem ipsum")