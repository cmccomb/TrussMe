import numpy

class Member(object):

    shape_names = ["pipe", "bar", "square", "box"]

    def __init__(self):
        # Shape independent variables
        self.t = 0.0   # thickness
        self.w = 0.0   # outer width
        self.h = 0.0   # outer height
        self.r = 0.0   # outer radius

        # Material properties
        self.Fy = 0.0  # yield strength
        self.rho = 0.0 # material density

        # Dependent variables
        self.A = 0.0   # Cross-sectional area
        self.I = 0.0   # Moment of inertia
        self.LW = 0.0  # Linear weight

        # Things that are started with default values
        self.shape = "pipe"
        self.material = ""
        self.calc_properties()

    def set_shape(self, new_shape):
        if self.shape_name_is_ok(new_shape):
            self.shape = new_shape
            self.calc_properties()
        else:
            raise ValueError(new_shape+' is not an defined shape. Try ' +
                             ', '.join(self.shape_names[0:-1]) + ', or ' +
                             self.shape_names[-1] + '.')


    def set_material(self, new_material):
        asdf = 1

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
            else:
                raise ValueError(key+' is not an defined shape. '
                                     'Try thickness (t), width (w), '
                                     'height (h), or radius (r).')


        # Check parameters
        if self.shape == "pipe":
            if
        if self.shape == "box":



    def calc_properties(self):
        # Calculate moment of inertia
        self.I = 0.0

        # Calculate the cross-sectional area

        # Calculate the



    def shape_name_is_ok(self, name):
        if name in self.shape_names:
            return True
        else:
            return False