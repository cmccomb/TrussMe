from numpy import pi, array, size, zeros, outer, ones, concatenate, where, \
    multiply, sum, column_stack, vstack, hstack, append, abs, mean, std, \
    loadtxt, diag, delete, inf, dot, atleast_2d, log, sqrt, isnan, isinf, \
    unique
from numpy.linalg import norm, solve, cond, det
from numpy.random import uniform, choice

import math
import copy

from matplotlib import delaunay
from matplotlib.pyplot import plot, axis, arrow, title, annotate, gca

# Yield strength of steel
Fy = 344*pow(10, 6)

# Elastic modulus of steel
E = 210*pow(10, 9)

# Outer diameters of the optional sizes, in meters
OUTER_DIAM = [(x+1.0)/100 for x in range(10)]

# Thickness of the wall sections of optional sizes, in meters
THICK = [d/15 for d in OUTER_DIAM]

# Cross sectional area in m^2
AREA_SEC = [pi*pow(d/2, 2) - pi*pow(d/2-d/15, 2) for d in OUTER_DIAM]

# Moment of inertia, in m^4
I_SEC = [pi*(pow(d, 4) - pow((d - 2*d/15), 4))/64 for d in OUTER_DIAM]

# Weight per length, kg/ft
WEIGHT = [a*7870 for a in AREA_SEC]

# Minimum required factor of safety
FOS_MIN = 1.25

# Mass target
MASS_TARGET = 175

# Constants to use for truss initialization
INITDIST = 2.0
INITREPS = 100
THETATOL = 0.25

# Constants to use for operational distance evaluation
DISTREPS = 10
SCRAMREPS = 40


class Truss(object):
    
    def __init__(self, n=None):
        if n is not None:        
            # Save number of joints
            self.n = n

            # Create first set of coordinates
            self.coord = array([[-5, 0, 0],
                                [-2, 0, 0],
                                [ 1, 0, 0],
                                [ 3, 0, 0],
                                [ 5, 0, 0]])

            # Draw randomly for joint locations
            for i in range(self.n-5):
                # Draw random location from distribution
                xy = self._draw_random_joint()
                self.coord = vstack([self.coord, xy])
            self.coord = self.coord.T

            # Delaunay triangulation to get connections
            cens, edg, tri, neig = matplotlib.delaunay.delaunay(self.coord[0, :], self.coord[1, :])
            self.con = edg.T

            # Check for near-redundant connections (angle)
            for j in range(self.n):
                row, col = where(self.con == j)
                theta = []
                length = []

                # Calculate angles of outgoing members
                for member in col:
                    other_end = self.con[:, member]
                    if other_end[0] == j:
                        other_end = other_end[1]
                    else:
                        other_end = other_end[0]

                    dx, dy, dz = self.coord[:, other_end] - self.coord[:, j]
                    theta.append(math.atan2(dy, dx))
                    length.append(norm([dx, dy]))
                removal_list = []

                # Check to see if any are close to one another
                for i in range(len(theta)):
                    for k in range(i, len(theta)):
                        if abs(theta[i] - theta[k]) < THETATOL:
                            if length[i] > length[k]:
                                removal_list.append(i)

                # Perform removal
                if removal_list is not []:
                    self.con = delete(self.con, [col[x] for x in removal_list], axis=1)

            # Store final number of members
            self.m = len(self.con.T)

            # Initialize truss sizes
            self.sizes = ones(len(self.con.T))*4

            # Establish the connectivity matrix
            self.con_mat = zeros([self.m, self.m])
            for member in self.con.T:
                self.con_mat[member[0], member[1]] = 1.0
                self.con_mat[member[1], member[0]] = 1.0

            # Evaluate the truss
            self.force = [0.0]
            self.fos = array([0.0])
            self.mass = 0.0
                
    def truss_eval(self):
        self.mass_eval()
        self.fos_eval()
                
    def mass_eval(self): 
        """This function calculates the mass of the truss"""
        # Calculate lengths
        L = zeros(self.m)
        for i in range(self.m):
            L[i] = norm(self.coord[:, self.con[0, i]] - self.coord[:, self.con[1, i]])

        # Calculate total mass
        self.mass = 0
        for i in range(self.m):
            self.mass += L[i]*WEIGHT[int(self.sizes[i])]
    
    def fos_eval(self):
        support = array([[1, 1, 1], [0, 0, 1], [0, 1, 1], [0, 0, 1], [1, 1, 1]]).T

        D = {"Re":  support}
        for _ in range(self.n-5):
            D["Re"] = column_stack([D["Re"], [0,0,1]])

        # Add the appropriate loads
        D["Load"] = zeros([3, self.n])
        D["Load"][1, 1] = -200000.0
        D["Load"][1, 3] = -200000.0

        # Add the area information from truss structure
        D["A"] = []
        for member_size in self.sizes:
            D["A"].append(AREA_SEC[int(member_size)])
        D["Coord"] = self.coord
        D["Con"] = self.con
        D["E"] = E*ones(self.m)

        # Do force analysis
        try:
            self.force, U, R = self._force_eval(D)
        except:
            self.force = ones(self.m)*pow(10, 16)
            
        # Calculate lengths
        L = zeros(self.m)
        for i in range(self.m):
            L[i] = norm(D["Coord"][:, D["Con"][0, i]] - D["Coord"][:, D["Con"][1, i]])

        # Calculate FOS's
        self.fos = zeros(self.m)
        for i in range(len(self.force)):
            self.fos[i] = D["A"][i]*Fy/self.force[i]
            if self.fos[i] < 0:
                self.fos[i] = min(pi*pi*E*I_SEC[int(self.sizes[i] - 1)]/(L[i]*L[i])/-self.force[i], -self.fos[i])
    
        # Make sure loads and supports are connected
        for i in range(5):
            if size(where(self.con == i)) == 0:
                self.fos = zeros(self.m)
        
        if isnan(sum(self.fos)):
            self.fos = zeros(self.m)
        
        for i in range(self.m):
            if isinf(self.fos[i]):
                self.fos[i] = pow(10,10)
                
    def single_member(self, j, inc_dec):
        self.sizes[j] += inc_dec
        if self.sizes[j] > 9.0:
            self.sizes[j] = 9.0
        if self.sizes[j] < 0.0:
            self.sizes[j] = 0.0
    
    def add_joint(self, xy):
        self.n += 1

        temp = zeros([self.n, self.n])
        for i in range(self.n-1):
            for j in range(self.n-1):
                temp[i, j] = self.con_mat[i, j]
                
        self.con_mat = temp
        self.coord = vstack([self.coord.T, xy]).T
        
    def move_joint(self, j, dxy):
        self.coord[:, j] += dxy
        
    def delete_joint(self, j):
        # Remove from coordinate list
        self.coord = delete(self.coord, j, 1)

        # Remove row and column from conn_mat
        self.con_mat = delete(self.con_mat, j, 0)
        self.con_mat = delete(self.con_mat, j, 1)

        # Remove connected members
        _, col = where(self.con == j)
        self.con = delete(self.con, col, 1)
        self.sizes = delete(self.sizes, col)
        self.m -= len(col)

        # Decrement connections appropriately
        for i in range(self.m):
            if self.con[0, i] > j:
                self.con[0, i] -=1
            if self.con[1, i] > j:
                self.con[1, i] -=1

        # Decrement number of joints
        self.n -=1

    def add_member(self, a, b):
        self.con = vstack([self.con.T, array([a, b])]).T
        self.con_mat[a, b] = 1.0
        self.con_mat[b, a] = 1.0
        self.sizes = hstack([self.sizes, array(4.0)])
        self.m += 1
        
    def delete_member(self, j):
        self.con_mat[self.con[1, j], self.con[0, j]] = 0.0
        self.con_mat[self.con[0, j], self.con[1, j]] = 0.0
        self.con = delete(self.con, j, 1)        
        self.sizes = delete(self.sizes, j)
        self.m -= 1
    
    def _draw_random_joint(self):
        mind = []
        xysave = []
        for i in range(INITREPS):
            xy = uniform([-6.0, -6.0], [6.0, 6.0], 2)
            d = []
            for joint in self.coord:
                d.append(norm(joint - xy))
            dmin1 = min(d)
            d.remove(dmin1)
            dmin2 = min(d)
            mind.append(abs(dmin1 - INITDIST) + abs(dmin2 - INITDIST))
            xysave.append(xy)
        idx = array(mind).argmin()
        return xysave[idx]
    
    def _force_eval(self, D):
        Tj = zeros([3, size(D["Con"], axis=1)])
        w = array([size(D["Re"], axis=0), size(D["Re"], axis=1)])
        SS = zeros([3*w[1], 3*w[1]])
        U = 1.0 - D["Re"]

        # This identifies joints that are unsupported, and can therefore be loaded
        ff = where(U.T.flat == 1)[0]

        # Step through the each member in the truss, and build the global stiffness matrix
        for i in range(size(D["Con"], axis=1)):
            H = D["Con"][:, i]
            C = D["Coord"][:, H[1]] - D["Coord"][:, H[0]]
            Le = norm(C)
            T = C/Le
            s = outer(T, T)
            G = D["E"][i]*D["A"][i]/Le
            ss = G*concatenate((concatenate((s, -s), axis=1), concatenate((-s, s), axis=1)), axis=0)
            Tj[:, i] = G*T
            e = range((3*H[0]), (3*H[0] + 3)) + range((3*H[1]), (3*H[1] + 3))
            for ii in range(6):
                for j in range(6):
                    SS[e[ii], e[j]] += ss[ii, j]

        SSff = zeros([len(ff), len(ff)])
        for i in range(len(ff)):
            for j in range(len(ff)):
                SSff[i,j] = SS[ff[i], ff[j]]

        Loadff = D["Load"].T.flat[ff]
        Uff = solve(SSff, Loadff)

        ff = where(U.T==1)
        for i in range(len(ff[0])):
            U[ff[1][i], ff[0][i]] = Uff[i]
        F = sum(multiply(Tj, U[:, D["Con"][1,:]] - U[:, D["Con"][0,:]]), axis=0)
        if cond(SSff) > pow(10,10):
            F *= pow(10, 10)
        R = sum(SS*U.T.flat[:], axis=1).reshape([w[1], w[0]]).T

        return F, U, R

    def __sub__(self, other):

        nA = self.n
        nB = other.n

        # Define a function to calculate static distance
        stat_dist = lambda x, y: sum(abs(x - y))

        # Get the connectivity matrices specifically
        A = self.con_mat.copy() 
        B = other.con_mat.copy()

        # Resize if necessary
        if len(A) > len(B):
            dim = len(A)
            temp = zeros([dim, dim])
            for i in range(len(B)):
                for j in range(len(B)):
                    temp[i, j] = B[i, j]
            B = temp
        elif len(B) > len(A):
            dim = len(B)
            temp = zeros([dim, dim])
            for i in range(len(A)):
                for j in range(len(A)):
                    temp[i, j] = B[i, j]
            A = temp
        L = len(A)
        best_dist = stat_dist(A, B)


        attempt = []
        for t in range(DISTREPS):
            for i in range(5, L):
                for j in range(i, L):
                    # Make temp copy
                    temp = A.copy()
                    # Swap columns
                    temp[:, [i, j]] = temp[:, [j, i]]
                    # Swap rows
                    temp[[i, j], :] = temp[[j, i], :]

                    # Evaluate
                    temp_dist = stat_dist(temp, B)
                    if temp_dist < best_dist:
                        best_dist = temp_dist
                        A = temp

                    attempt.append(temp_dist)

            # Scramble and re-start
            for i in range(SCRAMREPS):
                a = choice(range(5, L))
                b = choice(range(5, L))
                # Swap columns
                A[:, [a, b]] = A[:, [b, a]]
                # Swap rows
                A[[a, b], :] = A[[b, a], :]

        return best_dist/2 + abs(nA - nB)


    def copy(self):
        """This function allows the truss to be safely copied"""
        
        # Make a blank truss
        new_truss = Truss()
        new_truss.script = []
        
        # Copy the truss construction info
        new_truss.m = copy.copy(self.m)
        new_truss.n = copy.copy(self.n)
        new_truss.con = copy.copy(self.con)
        new_truss.coord = copy.copy(self.coord)
        new_truss.sizes = copy.copy(self.sizes)
        new_truss.con_mat = copy.copy(self.con_mat)
        
        # Copy the truss performance info
        new_truss.fos = copy.copy(self.fos)
        new_truss.force = copy.copy(self.force)
        new_truss.mass = copy.copy(self.mass)
        
        return new_truss


# This function plots the truss, labeling with FOS
def plot_truss(truss, LABELS=True):
    # Plot every member
    for i in range(truss.m):
        p1 = truss.coord[:, truss.con[0, i]]
        p2 = truss.coord[:, truss.con[1, i]]
        if truss.fos[i] > FOS_MIN:
            color = 'g'
        else:
            color = 'r'
        if truss.force[i] > 0:
            lst = '--'
        else:
            lst = '-'
        xyz = (p1+p2)/2
        if truss.fos[i] < 10.0:
            trstr = "{0:.2f}".format(truss.fos[i])
        else:
            trstr = ">10.0"
        if LABELS:
            matplotlib.pyplot.annotate(trstr, [xyz[0], xyz[1]], bbox=dict(boxstyle="round", fc="w")) 
        matplotlib.pyplot.plot([p1[0], p2[0]], [p1[1], p2[1]], color, linewidth=truss.sizes[i]+1, linestyle = lst);
        matplotlib.pyplot.axis('equal')
        
    # Plot supports
    matplotlib.pyplot.plot(truss.coord[0, 0], truss.coord[1, 0], 'ks', ms=15);
    matplotlib.pyplot.plot(truss.coord[0, 2], truss.coord[1, 2], 'ko', ms=15);
    matplotlib.pyplot.plot(truss.coord[0, 4], truss.coord[1, 4], 'ks', ms=15);
    
    # Plot loads
    matplotlib.pyplot.plot(truss.coord[0, 1], truss.coord[1, 1], 'ko', ms=10);
    matplotlib.pyplot.arrow(truss.coord[0, 1], truss.coord[1, 1] + 2.0, 0.0, -1.5, 
                    fc="m", ec="m", head_width=0.3, head_length=0.6, width=0.1, zorder=3);
    matplotlib.pyplot.plot(truss.coord[0, 3], truss.coord[1, 3], 'ko', ms=10);
    matplotlib.pyplot.arrow(truss.coord[0, 3], truss.coord[1, 3] + 2.0, 0.0, -1.5, 
                    fc="m", ec="m", head_width=0.3, head_length=0.6, width=0.1, zorder=3);
        
    # Plot every joint
    for i in range(truss.n-5):
        matplotlib.pyplot.plot(truss.coord[0, i + 5], truss.coord[1, i + 5], 'ko', ms=10);
    
    # Make the title
    matplotlib.pyplot.title("FOS = "+"{0:.4f}".format(min(truss.fos))+", Mass = "+"{0:.2f}".format(truss.mass)+"kg")
    
    matplotlib.pyplot.gca().set_xlim([-6, 6])
    matplotlib.pyplotgca().set_ylim([-6, 6])
