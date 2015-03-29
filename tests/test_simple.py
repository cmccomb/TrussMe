import numpy
from trussme import truss
import unittest

class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.T = truss.Truss()

    def test_joints(self):
        self.T.add_support(numpy.array([0.0, 0.0, 0.0]), d=2)
        self.T.add_joint(numpy.array([1.0, 1.0, 0.0]), d=2)
        self.T.add_support(numpy.array([2.0, 0.0, 0.0]), d=2)
        self.T.add_joint(numpy.array([1.0, 0.0, 0.0]), d=2)

        self.T.add_member(0, 1)
        self.T.add_member(1, 2)
        self.T.add_member(2, 3)
        self.T.add_member(3, 0)
        self.T.add_member(1, 3)
        
        for m in self.T.members:
            print(m.idx)
            
        self.T.move_joint(2, numpy.array([5.0, 5.0, 5.0]))
        print(self.T.joints[2].coordinates)
        print(self.T.members[1].joints[0].coordinates)
        print(self.T.members[1].joints[1].coordinates)
        print(self.T.members[2].joints[0].coordinates)
        print(self.T.members[2].joints[1].coordinates)

if __name__ == "__main__":
    unittest.main()
