import numpy


class Joint(object):
    
    # Saving the number of joints
    number_of_joints = 0

    def __init__(self, coordinates):
        # Save the joint id
        self.idx = self.number_of_joints
        Joint.number_of_joints += 1

        # Coordinates of the joint
        self.coordinates = coordinates

        # Allowed translation in x, y, and z
        self.translation = numpy.ones([3, 1], dtype=bool)

        # Loads
        self.loads = numpy.zeros([3, 1])

        # Store connected members
        self.members = []

    def free(self, d=3):
        self.translation = numpy.ones([3, 1], dtype=bool)
        # If 2d, add out of plane support
        if d is 2:
            self.translation[2] = False

    def pinned(self, d=3):
        # Restrict all translation
        self.translation = numpy.zeros([3, 1], dtype=bool)

        # If 2d, add out of plane support
        if d is 2:
            self.translation[2] = False

    def roller(self, axis='y', d=3):
        # Only support reaction along denotated axis
        self.translation = numpy.ones([3, 1], dtype=bool)
        self.translation[ord(axis)-120] = False

        # If 2d, add out of plane support
        if d is 2:
            self.translation[2] = False
