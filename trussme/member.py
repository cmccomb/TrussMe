import numpy
import warnings


class Member(object):
    
    # Save the number of members
    number_of_members = 0

    # Shape types
    shapes = ["pipe", "bar", "square", "box"]

    # Material options and characteristics
    #            name     rho   E               Fy
    materials = {"A36":  [7800, 200*pow(10, 9), 250*pow(10, 6)],
                 "A992": [7850, 200*pow(10, 9), 345*pow(10, 6)]}

    def __init__(self, joint_a, joint_b):
        # Save id number
        self.idx = self.number_of_members
        Member.number_of_members += 1

        # Shape independent variables
        self.shape = ''
        self.t = 0.0  # thickness
        self.w = 0.0  # outer width
        self.h = 0.0  # outer height
        self.r = 0.0  # outer radius

        # Material properties
        self.material = ''  # string specifying material
        self.E = 0.0        # Elastic modulus
        self.Fy = 0.0       # yield strength
        self.rho = 0.0      # material density

        # Dependent variables
        self.A = 0.0   # Cross-sectional area
        self.I = 0.0   # Moment of inertia
        self.LW = 0.0  # Linear weight

        # Variables to store information about truss state
        self.force = 0
        self.fos_yield = 0
        self.fos_buckling = 0
        self.mass = 0

        # Variable to store location in truss
        self.joints = [joint_a, joint_b]
        self.length = 0
        self.end_a = []
        self.end_b = []

        # Calculate properties
        self.set_shape("pipe", update_props=False)
        self.set_material("A36", update_props=False)
        self.set_parameters(t=0.01, r=0.1, update_props=True)

    def set_shape(self, new_shape, update_props=True):
        # Read and save hte shape name
        if self.shape_name_is_ok(new_shape):
            self.shape = new_shape
        else:
            raise ValueError(new_shape+' is not a defined shape. Try ' +
                             ', '.join(self.shapes[0:-1]) + ', or ' +
                             self.shapes[-1] + '.')

        # If required, update properties
        if update_props:
            self.calc_properties()

    def set_material(self, new_material, update_props=True):
        if self.material_name_is_ok(new_material):
            self.material = new_material
        else:
            raise ValueError(new_material+' is not a defined shape. Try ' +
                             ', '.join(self.materials.keys()[0:-1]) + ', or ' +
                             self.materials.keys()[-1] + '.')

        # Set material properties
        self.rho = self.materials[new_material][0]
        self.E = self.materials[new_material][1]
        self.Fy = self.materials[new_material][2]

        # If required, update properties
        if update_props:
            self.calc_properties()

    def set_parameters(self, **kwargs):
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
                self.calc_properties()
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
        elif self.shape == "box":
            self.I = (1./12.)*self.w*self.h**3
        elif self.shape == "square":
            self.I = (1./12.)*(self.w*self.h**3)\
                - (1./12.)*(self.w - 2*self.t)*(self.h - 2*self.t)**3

    def calc_area(self):
        if self.shape == "pipe":
            self.A = numpy.pi*(self.r**2 - (self.r-self.t)**2)
        elif self.shape == "bar":
            self.A = numpy.pi*self.r**2
        elif self.shape == "box":
            self.A = self.w*self.h - (self.h - 2*self.t)*(self.w - 2*self.t)
        elif self.shape == "square":
            self.A = self.w * self.h

    def calc_lw(self):
        self.LW = self.A * self.rho

    def calc_geometry(self):
        self.end_a = self.joints[0].coordinates
        self.end_b = self.joints[1].coordinates
        self.length = numpy.linalg.norm(self.end_a - self.end_b)
        self.mass = self.length*self.LW

    def update_joints(self, joint_a, joint_b):
        self.joints = [joint_a, joint_b]
        self.calc_geometry()

    def shape_name_is_ok(self, name):
        if name in self.shapes:
            return True
        else:
            return False

    def material_name_is_ok(self, name):
        if name in self.materials.keys():
            return True
        else:
            return False
