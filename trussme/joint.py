import numpy
from numpy.typing import NDArray
from typing import Literal


class Joint(object):

    def __init__(self, coordinates: list[float]):
        # Save the joint id
        self.idx: int = -1

        # Coordinates of the joint
        self.coordinates = coordinates

        # Allowed translation in x, y, and z
        self.translation = [True, True, True]

        # Loads
        self.loads: list[float] = [0.0, 0.0, 0.0]

        # Store connected members
        self.members = []

        # Loads
        self.reactions = numpy.zeros([3, 1])

        # Loads
        self.deflections = numpy.zeros([3, 1])

    def free(self, d: int = 3):
        self.translation = [False, False, False]
        # If 2d, add out of plane support
        if d is 2:
            self.translation[2] = True

    def pinned(self, d: int = 3):
        # Restrict all translation
        self.translation = [True, True, True]

    def roller(self, axis: Literal["x", "y"] = 'y', d: int = 3):
        # Only support reaction along denoted axis
        self.translation = [False, False, False]
        self.translation[ord(axis)-120] = True

        # If 2d, add out of plane support
        if d is 2:
            self.translation[2] = True
