import numpy


class Joint(object):

    def __init__(self, idx=-1):
        # Save the joint id
        self.idx = idx

        # Coordinates of the joint
        self.coordinates = numpy.zeros([1, 3])

        # Allowed translation in x, y, and z
        self.translation = numpy.ones([1, 3], dtype=bool)

        # Allow rotation about x, y, or z
        self.rotation = numpy.ones([1, 3], dtype=bool)

        # Loads
        self.loads = numpy.zeros([1, 3])

    def free(self, d=3):
        self.translation = numpy.ones([1, 3], dtype=bool)
        self.rotation = numpy.ones([1, 3], dtype=bool)
        # If 2d, add out of plane support, and restrict to in-plane rotation
        if d is 2:
            self.translation[2] = False
            self.rotation[0] = False
            self.rotation[1] = False

    def fixed(self):
        self.translation = numpy.zeros([1, 3], dtype=bool)
        self.rotation = numpy.zeros([1, 3], dtype=bool)

    def d3_pinned(self, d=3):
        # Restrict all translation, but allow rotation
        self.translation = numpy.zeros([1, 3], dtype=bool)
        self.rotation = numpy.ones([1, 3], dtype=bool)

        # If 2d, add out of plane support, and restrict to in-plane rotation
        if d is 2:
            self.translation[2] = False
            self.rotation[0] = False
            self.rotation[1] = False


    def d3_roller(self, axis='y', d=3):
        # Only support reaction along denotated axis
        self.rotation = numpy.ones([1, 3], dtype=bool)
        self.rotation = numpy.ones([1, 3], dtype=bool)
        self.rotation[ord(axis)-120] = False

        # If 2d, add out of plane support, and restrict to in-plane rotation
        if d is 2:
            self.translation[2] = False
            self.rotation[0] = False
            self.rotation[1] = False

