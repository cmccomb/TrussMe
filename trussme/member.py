import numpy
import warnings
from trussme.physical_properties import Material, MATERIALS
from trussme.joint import Joint
from typing import Literal, Union


class Pipe(object):
    def __init__(self, r: float, t: float):
        self.r: float = r
        self.t: float = t

    def moi(self) -> float:
        return (numpy.pi / 4.) * (self.r ** 4 - (self.r - 2 * self.t) ** 4)

    def area(self) -> float:
        return numpy.pi * (self.r ** 2 - (self.r - self.t) ** 2)


class Bar(object):
    def __init__(self, r: float):
        self.r: float = r

    def moi(self) -> float:
        return (numpy.pi / 4.) * self.r ** 4

    def area(self) -> float:
        return numpy.pi*self.r**2


class Square(object):
    def __init__(self, w: float, h: float):
        self.w: float = w
        self.h: float = h

    def moi(self) -> float:
        if self.h > self.w:
            return (1./12.)*self.w*self.h**3
        else:
            return (1./12.)*self.h*self.w**3

    def area(self) -> float:
        return self.w * self.h

class Box(object):
    def __init__(self, w: float, h: float, t: float):
        self.w: float = w
        self.h: float = h
        self.t: float = t

    def moi(self) -> float:
        if self.h > self.w:
            return (1./12.)*(self.w*self.h**3)\
                - (1./12.)*(self.w - 2*self.t)*(self.h - 2*self.t)**3
        else:
            return (1./12.)*(self.h*self.w**3)\
                - (1./12.)*(self.h - 2*self.t)*(self.w - 2*self.t)**3

    def area(self) -> float:
        return self.w*self.h - (self.h - 2*self.t)*(self.w - 2*self.t)


Shape = Union[Pipe, Bar, Square, Box, None]


class Member(object):

    # Shape types
    shapes: list[str] = ["pipe", "bar", "square", "box"]

    def __init__(self, joint_a: Joint, joint_b: Joint):
        # Save id number
        self.idx = -1

        # Shape independent variables
        self.shape: Shape = None
        self.t: float = 0.0  # thickness
        self.w: float = 0.0  # outer width
        self.h: float = 0.0  # outer height
        self.r: float = 0.0  # outer radius

        # Material properties
        self.material: str = ''  # string specifying material
        self.elastic_modulus: float = 0.0        # Elastic modulus
        self.Fy: float = 0.0       # yield strength
        self.rho: float = 0.0      # material density

        # Dependent variables
        self.area: float = 0.0   # Cross-sectional area
        self.I: float = 0.0   # Moment of inertia
        self.LW: float = 0.0  # Linear weight

        # Variables to store information about truss state
        self.force: float = 0
        self.fos_yielding: float = 0
        self.fos_buckling: float = 0
        self.mass: float = 0

        # Variable to store location in truss
        self.joints = [joint_a, joint_b]
        self.length: float = 0.0
        self.end_a = []
        self.end_b = []

        # Calculate properties
        self.set_shape("pipe", update_props=False)
        self.set_material(MATERIALS[0], update_props=False)
        self.set_parameters(t=0.002, r=0.02, update_props=True)

    def set_shape(self, new_shape: Literal["pipe", "bar", "square", "box"], update_props: bool = True):
        # Read and save hte shape name
        if self.shape_name_is_ok(new_shape):
            self.shape = new_shape
        else:
            raise ValueError(new_shape+' is not a defined shape. Try ' +
                             ', '.join(self.shapes[0:-1]) + ', or ' +
                             self.shapes[-1] + '.')

        if self.shape is "pipe":
            self.w = "N/A"
            self.h = "N/A"
        elif self.shape is "bar":
            self.w = "N/A"
            self.h = "N/A"
            self.r = "N/A"
        elif self.shape is "square":
            self.r = "N/A"
            self.t = "N/A"
        elif self.shape is "box":
            self.r = "N/A"

        # If required, update properties
        if update_props:
            self.calc_properties()

    def set_material(self, new_material: Material, update_props: bool = True):
        # Set material properties
        self.material = new_material["name"]
        self.rho = new_material["rho"]
        self.elastic_modulus = new_material["E"]
        self.Fy = new_material["Fy"]

        # If required, update properties
        if update_props:
            self.calc_properties()

    def set_parameters(self, **kwargs):
        prop_update = False
        # Save the values
        for key in kwargs.keys():
            if key is "radius":
                self.r = kwargs["radius"]
            elif key is "r":
                self.r = kwargs["r"]
            elif key is "thickness":
                self.t = kwargs["thickness"]
            elif key is "t":
                self.t = kwargs["t"]
            elif key is "width":
                self.w = kwargs["width"]
            elif key is "w":
                self.w = kwargs["w"]
            elif key is "height":
                self.h = kwargs["height"]
            elif key is "h":
                self.h = kwargs["h"]
            elif kwargs["update_props"]:
                prop_update = True
            else:
                raise ValueError(key+' is not an defined shape. '
                                     'Try thickness (t), width (w), '
                                     'height (h), or radius (r).')

        # Check parameters
        if self.shape == "pipe":
            if self.t > self.r:
                warnings.warn("Thickness is greater than radius."
                              "Changing shape to bar.")
        if self.shape == "box":
            if 2*self.t > self.w:
                warnings.warn("Thickness is greater than half of width."
                              "Changing shape to square.")
            elif 2*self.t > self.h:
                warnings.warn("Thickness is greater than half of height."
                              "Changing shape to square.")

        if prop_update:
            self.calc_properties()

    def calc_properties(self):
        # Calculate moment of inertia
        self.calc_moi()

        # Calculate the cross-sectional area
        self.calc_area()

        # Calculate the linear mass
        self.calc_lw()

        # Update length, etc.
        self.calc_geometry()

    def calc_moi(self):
        if self.shape == "pipe":
            self.I = (numpy.pi/4.)*(self.r**4 - (self.r - 2*self.t)**4)
        elif self.shape == "bar":
            self.I = (numpy.pi/4.)*self.r**4
        elif self.shape == "square":
            if self.h > self.w:
                self.I = (1./12.)*self.w*self.h**3
            else:
                self.I = (1./12.)*self.h*self.w**3
        elif self.shape == "box":
            if self.h > self.w:
                self.I = (1./12.)*(self.w*self.h**3)\
                    - (1./12.)*(self.w - 2*self.t)*(self.h - 2*self.t)**3
            else:
                self.I = (1./12.)*(self.h*self.w**3)\
                    - (1./12.)*(self.h - 2*self.t)*(self.w - 2*self.t)**3

    def calc_area(self):
        if self.shape == "pipe":
            self.area = numpy.pi*(self.r**2 - (self.r-self.t)**2)
        elif self.shape == "bar":
            self.area = numpy.pi*self.r**2
        elif self.shape == "box":
            self.area = self.w*self.h - (self.h - 2*self.t)*(self.w - 2*self.t)
        elif self.shape == "square":
            self.area = self.w * self.h

    def calc_lw(self):
        self.LW = self.area * self.rho

    def calc_geometry(self):
        self.end_a = self.joints[0].coordinates
        self.end_b = self.joints[1].coordinates
        self.length = numpy.linalg.norm(self.end_a - self.end_b)
        self.mass = self.length*self.LW

    def set_force(self, the_force):
        self.force = the_force
        self.fos_yielding = self.Fy/abs(self.force/self.area)
        self.fos_buckling = -((numpy.pi**2)*self.elastic_modulus*self.I
                             /(self.length**2))/self.force

    def update_joints(self, joint_a, joint_b):
        self.joints = [joint_a, joint_b]
        self.calc_geometry()

    def shape_name_is_ok(self, name):
        if name in self.shapes:
            return True
        else:
            return False


