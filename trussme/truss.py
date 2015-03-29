import numpy
from trussme import joint
from trussme import member

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
        for m in members:
            self.mass += m.mass

