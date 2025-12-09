#!/usr/bin/env python3

# Copyright (C) 2022-2023
#               Free Software Foundation, Inc.
# This file is part of Chisel.
#
# Chisel is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# Chisel is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Chisel; see the file COPYING.  If not, write to the
# Free Software Foundation, 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#
# Author Gaius Mulley <gaiusmod2@gmail.com>
#

import sys
import math

from decimal import Decimal

epsilon = 0.0001

#
#  printf - keeps C programmers happy :-)
#

def printf (format, *args):
    print (str (format) % args, end=' ')


#
#  error - issues an error message and exits.
#

def error (format, *args):
    print (str (format) % args, end=' ')
    raise
    # sys.exit (1)


def is_near (a, b):
    if isinstance (a, float) and isinstance (b, float):
        return abs (a - b) < epsilon
    if isinstance (a, int):
        return is_near (float (a), b)
    if isinstance (b, int):
        return is_near (a, float (b))
    return a == b

class vec:
    def __init__ (self, x, y, z, a=None):
        print ("vec __init__")
        self._x = Decimal (x)
        self._y = Decimal (y)
        self._z = Decimal (z)
        if a is None:
            self._dim = 3
            self._a = None
        else:
            self._a = Decimal (a)
            self._dim = 4
    def is_matrice (self):
        return False
    def is_vec (self):
        return True
    def __str__ (self):
        s = "vec (" + str (self._x)
        s += ', '
        s += str (self._y)
        s += ', '
        s += str (self._z)
        if self._a != None:
            s += ', '
            s += str (self._a)
        s += ')'
        return s
    def to_list (self, length = None):
        result = [self._x, self._y, self._z]
        if self._a != None:
            result += [self._a]
        return result
    def dup (self):
        return vec (self._x, self._y, self._z, self._a)
    def length (self):
        return self._dim
    def extend (self, length, value):
        if self._dim < length:
            self._a = value
            self._dim += 1
        return self
    def element (self, idx):
        if idx < self._dim:
            if idx == 0:
                return self._x
            if idx == 1:
                return self._y
            if idx == 2:
                return self._z
            if idx == 3:
                return self._a
        print (self, "idx =", idx, self._dim)
        error ("vec[idx] is out of bounds")
    def set_element (self, idx, value):
        value = Decimal (value)
        if idx < self._dim:
            if idx == 0:
                self._x = value
            if idx == 1:
                self._y = value
            if idx == 2:
                self._z = value
            if idx == 3:
                self._a = value
            return self
        print (self, "idx =", idx, self._dim)
        error ("vec[idx] is out of bounds")
    def init (self, value):
        value = Decimal (value)
        self._x = value
        self._y = value
        self._z = value
        if self._dim == 4:
            self._a = value
        return self
    def mult_vec (self, other):
        if self.length () != other.length ():
            error ("cannot multiply different vector lengths")
        result = self.dup ()
        result.init (0)
        print ("mult_vec start =", self)
        for idx in range (self.length ()):
            result.set_element (idx, self.element (idx) * other.element (idx))
        print ("mult_vec end =", self)
        print ("mult_vec result =", result)
        return result
    #
    #  mult_mat - multiply vector self by matrice mat.
    #
    def mult_mat (self, mat):
        assert (mat.is_matrice ())
        vector = self.dup ()
        print ("vector in mult_mat", vector)
        self.init (0)
        xprime = (vector.element (0) * mat.element (0, 0) +
                  vector.element (1) * mat.element (1, 0) +
                  vector.element (2) * mat.element (2, 0) +
                  mat.element (3, 0))
        self.set_element (0, xprime)
        yprime = (vector.element (0) * mat.element (0, 1) +
                  vector.element (1) * mat.element (1, 1) +
                  vector.element (2) * mat.element (2, 1) +
                  mat.element (3, 1))
        self.set_element (1, yprime)
        zprime = (vector.element (0) * mat.element (0, 2) +
                  vector.element (1) * mat.element (1, 2) +
                  vector.element (2) * mat.element (2, 2) +
                  mat.element (3, 2))
        self.set_element (2, zprime)
        print ("finished vec", self)
        return self
    def __eq__ (self, other):
        if other == None:
            return False
        if self.length () != other.length ():
            return False
        if not is_near (self._x, other._x):
            return False
        if not is_near (self._y, other._y):
            return False
        if not is_near (self._z, other._z):
            return False
        if not is_near (self._a, other._a):
            return False
        return True
    def __ne__ (self, other):
        if other == None:
            return True
        if self.length () != other.length ():
            return True
        if not is_near (self._x, other._x):
            return True
        if not is_near (self._y, other._y):
            return True
        if not is_near (self._z, other._z):
            return True
        if not is_near (self._a, other._a):
            return True
        return False
    def scale (self, factor):
        self._x *= factor
        self._y *= factor
        self._z *= factor
        if self._a != None:
            self._a *= factor
        return self
    def __add__ (self, other):
        if self._dim == other._dim:
            if self._dim == 3:
                return vec (self._x + other._x,
                            self._y + other._y,
                            self._z + other._z)
            elif self._dim == 4:
                return vec (self._x + other._x,
                            self._y + other._y,
                            self._z + other._z,
                            self._a + other._a)
        error ("can only add vectors of the same size")
    def __sub__ (self, other):
        if self._dim == other._dim:
            if self._dim == 3:
                return vec (self._x - other._x,
                            self._y - other._y,
                            self._z - other._z)
            elif self._dim == 4:
                return vec (self._x - other._x,
                            self._y - other._y,
                            self._z - other._z,
                            self._a - other._a)
        error ("can only sub vectors of the same size")
    def __neg__ (self):
        if self._dim == 3:
            return vec (-self._x, -self._y, -self._z)
        elif self._dim == 4:
            return vec (-self._x, -self._y, -self._z, -self._a)
class mat:
    def __init__ (self, x, y = None, z = None, a = None):
        if y is None:
            self._dim = x
            if x == 3:
                self._x = vec (Decimal (0.0), Decimal (0.0), Decimal (0.0))
                self._y = vec (Decimal (0.0), Decimal (0.0), Decimal (0.0))
                self._z = vec (Decimal (0.0), Decimal (0.0), Decimal (0.0))
                self._a = None
            else:
                self._x = vec (Decimal (0.0), Decimal (0.0), Decimal (0.0), Decimal (0.0))
                self._y = vec (Decimal (0.0), Decimal (0.0), Decimal (0.0), Decimal (0.0))
                self._z = vec (Decimal (0.0), Decimal (0.0), Decimal (0.0), Decimal (0.0))
                self._a = vec (Decimal (0.0), Decimal (0.0), Decimal (0.0), Decimal (0.0))
        else:
            self._x = x.dup ()
            self._y = y.dup ()
            self._z = z.dup ()
            if a == None:
                self._a = None
                self._dim = 3
            else:
                self._a = a.dup ()
                self._dim = 4
    def is_matrice (self):
        return True
    def is_vec (self):
        return False
    def __str__ (self):
        s = "mat ("
        s += str (self._x)
        s += ", "
        s += str (self._y)
        s += ", "
        s += str (self._z)
        if self._a != None:
            s += ", "
            s += str (self._a)
        s += ")"
        return s
    def init (self, value):
        self._x.init (value)
        self._y.init (value)
        self._z.init (value)
        if self._a != None:
            self._a.init (value)
    def identity (self):
        self.init (0)
        self._x.set_element (0, 1.0)
        self._y.set_element (1, 1.0)
        self._z.set_element (2, 1.0)
        if self._a != None:
            self._a.set_element (3, 1.0)
        print ("after identify", self)
    def length (self):
        return self._dim
    def dup (self):
        return mat (self._x, self._y, self._z, self._a)
    def element (self, col, row):
        if col == 0:
            return self._x.element (row)
        if col == 1:
            return self._y.element (row)
        if col == 2:
            return self._z.element (row)
        if col == 3:
            return self._a.element (row)
    def set_element (self, col, row, value):
        if col == 0:
            self._x.set_element (row, Decimal (value))
        if col == 1:
            self._y.set_element (row, Decimal (value))
        if col == 2:
            self._z.set_element (row, Decimal (value))
        if col == 3:
            self._a.set_element (row, Decimal (value))
    def mult_vec (self, vec):
        assert (vec.is_vec ())
        result = self.dup ()
        vec = vec.extend (self.length (), 1.0)
        result.init (0)
        for row in range (self.length ()):
            for col in range (self.length ()):
                if vec.length () < self.length ():
                    result.set_element (col, row,
                                        self.element (col, row) * vec.element (row))
                else:
                    result.set_element (col, row, self.element (col, row))
        return result
    def mult_mat (self, m):
        assert (m.is_matrice ())
        self.init (0)
        left = self.dup ()
        for col in range (self._dim):
            for row in range (self._dim):
                temp = 0
                for d in range (self._dim):
                    temp += left.get_element (d, row) * m.get_element (col, d)
                self.set_element (col, row, temp)
        return self
    def add_mat (self, m):
        assert (m.is_matrice ())
        result = self.dup ()
        result.init (0)
        for row in range (self._dim):
            for col in range (self._dim):
                result.set_element (col, row, self.get_element (col, row) + m.get_element (col, row))
        return result
    def add_vec (self, vec):
        assert (vec.is_vec ())
        for row in range (self._dim):
            for col in range (self._dim):
                self.set_element (col, row, self.get_element (col, row) + vec[col])
        return self
    def sub (self, m):
        assert (m.is_matrice ())
        pass
    def translate (self, vec):
        assert (vec.is_vec ())
        print ("mat.translate", vec)
        self.identify ()
        if self.length () == 4:
            if vec.length () < 3:
                error ("translate: vec must contain at least 3 elements")
            print ("create a translation matrice based on", vec)
            for col in range (self._dim):
                if col <= 2:
                    self.set_element (col).set_element (3, vec.element (col))
            print ("finishing translate matrice", self)
            return self
        error ("translate: only dimension 4 understood")
    def _radian (self, degree):
        return Decimal (degree) * Decimal (math.pi) / Decimal (180.0)
    def rotate_x (self, angle):
        if self._dim == 2:
            error ("rotate_x: unimplemented")
        elif self._dim == 3:
            radian = self._radian (angle)
            # self._elements = [1, 0, 0,
            #                   0, math.cos (radian), -math.sin (radian),
            #                   0, math.sin (radian), math.cos (radian)]
            error ("rotate_x: unimplemented")
            return self
        elif self._dim == 4:
            radian = self._radian (angle)
            self.init (0)
            self.set_element (0, 0, 1.0)
            self.set_element (3, 3, 1.0)
            self.set_element (1, 1, math.cos (-radian))
            self.set_element (1, 2, -math.sin (-radian))
            self.set_element (2, 1, math.sin (-radian))
            self.set_element (2, 2, math.cos (-radian))
            #  [1, 0, 0, 0,
            #   0, math.cos (-radian), -math.sin (-radian), 0,
            #   0, math.sin (-radian), math.cos (-radian), 0,
            #   0, 0, 0, 1]
            return self
        error ("rotate_x: implementation restriction only dimensions 2, 3 and 4 understood")
    def rotate_y (self, angle):
        if self._dim == 2:
            return self.rotate (angle)
        elif self._dim == 3:
            radian = self._radian (angle)
            self._elements = [math.cos (radian), 0, math.sin (radian),
                              0, 1, 0,
                              -math.sin (radian), 0, math.cos (radian)]
            return self
        elif self._dim == 4:
            radian = self._radian (angle)
            self.init (0)
            self.set_element (0, 0, 1.0)
            self.set_element (3, 3, 1.0)
            self.set_element (1, 1, math.cos (-radian))
            self.set_element (1, 2, math.sin (-radian))
            self.set_element (2, 1, -math.sin (-radian))
            self.set_element (2, 2, math.cos (-radian))
            #  [1, 0, 0, 0,
            #   0, math.cos (-radian), math.sin (-radian), 0,
            #   0, -math.sin (-radian), math.cos (-radian), 0,
            #   0, 0, 0, 1]
            return self
        error ("rotate_x: implementation restriction only dimensions 2, 3 and 4 understood")
    def rotate_z (self, angle):
        if self._dim == 2:
            return self.rotate (angle)
        elif self._dim == 3:
            radian = self._radian (angle)
            self._elements = [math.cos (radian), -math.sin (radian), 0,
                              math.sin (radian), math.cos (radian), 0,
                              0, 0, 1]
            return self
        elif self._dim == 4:
            radian = self._radian (angle)
            self.init (0)
            self.set_element (3, 3, 1.0)
            self.set_element (2, 2, 1.0)
            self.set_element (0, 0, math.cos (-radian))
            self.set_element (0, 1, -math.sin (-radian))
            self.set_element (1, 0, math.sin (-radian))
            self.set_element (1, 1, math.cos (-radian))
            #  [math.cos (-radian), -math.sin (-radian), 0, 0,
            #   math.sin (-radian), math.cos (-radian), 0, 0,
            #   0, 0, 1, 0,
            #   0, 0, 0, 1]
            return self
        error ("rotate_x: implementation restriction only dimensions 2, 3 and 4 understood")
    #
    #  scale - returns a matrice which contains a scale for each dimension.
    #
    def scale (self, vec):
        assert (vec.is_vec ())
        result = mat (self.length ())
        result.zeros ()
        print ("dim =, ", self._dim, vec, self._elements)
        for d in range (self._dim):
            print ("d =", d)
            if d < vec.length ():
                result.set_element (d, d, vec.element (d))
            else:
                result.set_element (d, d, 1)
        print ("finished scale", result)
        return result
    def translate (self, vec):
        assert (vec.is_vec ())
        result = mat (self.length ())
        result.zeros ()
        result.identity ()
        print (result)
        for d in range (self._dim -1):
            print (self._dim-1, d)
            result.set_element (self._dim -1, d, vec.element (d))
        return result
    def reflect_x (self):
        self.identity ()
        self.set_element (0, 0, -1.0)
        return self
    def reflect_y (self):
        self.identity ()
        self.set_element (1, 1, -1.0)
        return self
    def reflect_z (self):
        self.identity ()
        self.set_element (2, 2, -1.0)
        return self
    def ones (self):
        self._elements = [1] * self._dim * self._dim
        return self
    def zeros (self):
        self._elements = [0] * self._dim * self._dim
        return self

#
#  faces and vertices of the cube (ascii art)
#
#                                       6 +-------------+ 7
#                                        /.            /|
#                                       / .           / |
#                                      /  .          /  |
#    6+-----+7                      5 +-------------+ 4 |
#    /|    /|                         |   .         |   |
#  5+-----+4|                  y axis | 0 +.............+ 1
#   | |   | |                         |  /          |  /
#   |0+---|-+1                        | /Z axis     | /
#   |/    |/                          |/            |/
#  3+-----+2                        3 +-------------+ 2
#                                         x axis
#
#
#   Vertice 0:     (0, 0, 0)
#           1:     (1, 0, 0)
#           2:     (1, 0, 1)
#           3:     (0, 0, 1)
#           4:     (1, 1, 1)
#           5:     (0, 1, 1)
#           6:     (0, 1, 0)
#           7:     (1, 1, 0)
#
#
#   all labelled anti-clockwise when viewed from the front.
#   (rotate the cube so that the face is closest to the viewer).
#
#   faces = [[2, 4, 3, 5],    #  front
#            [1, 7, 2, 4],    #  right
#            [3, 5, 0, 6],    #  left
#            [6, 7, 0, 1],    #  back
#            [5, 4, 6, 7],    #  top
#            [3, 0, 2, 1]]    #  bottom

class poly:
    def __init__ (self, vertices = []):
        self._no_faces = 0
        self._vertices = vertices
        self._labels = {}
        self._faces = []
        self._textures = []
    def is_matrice (self):
        return False
    def unit_cube (self):
        self._no_faces = 6
        self._textures = ["wall"] * 6
        self._faces = [[2, 4, 3, 5],    #  front
                       [1, 7, 2, 4],    #  right
                       [3, 5, 0, 6],    #  left
                       [6, 7, 0, 1],    #  back
                       [5, 4, 6, 7],    #  top
                       [3, 0, 2, 1]]    #  bottom
        self._labels = {'front' :0,
                        'right' :1,
                        'left'  :2,
                        'back'  :3,
                        'top'   :4,
                        'bottom':5,
                        'a'     :0,
                        'b'     :1,
                        'c'     :2,
                        'd'     :3,
                        'e'     :4,
                        'f'     :5,
                        'g'     :6,
                        'h'     :7}
        self._vertices = [vec (0, 0, 0),  #  a
                          vec (1, 0, 0),  #  b
                          vec (1, 0, 1),  #  c
                          vec (0, 0, 1),  #  d
                          vec (1, 1, 1),  #  e
                          vec (0, 1, 1),  #  f
                          vec (0, 1, 0),  #  g
                          vec (1, 1, 0)]  #  h
        self.sanity_check ()
        return self
    def vertice_list (self):
        return 'abcdefgh'
    def sort_vert (self, vertices, dim, up):
        print ("*****************************")
        print ("sort_vert")
        copy = []
        for vert in vertices:
            copy += [vert.dup ()]
        vertices = copy
        self.dump_vertice_list (vertices)
        print (vertices)
        result = []
        while vertices != []:
            maximum = vertices[0]
            for vect in vertices:
                assert (vert.is_vec ())
                if vect.element (dim) > maximum.element (dim):
                    maximum = vect
            result += [maximum]
            vertices.remove (maximum)
        if not up:
            result.reverse ()
        return result
    def bisect (self, vertices):
        if len (vertices) == 8:
            return vertices[4:]
        if len (vertices) == 4:
            return vertices[2:]
        if len (vertices) == 2:
            return [vertices[1]]
        assert (false)
    def get_vertice (self, vertices, max_x, max_y, max_z):
        print ("get_vertice")
        self.dump_vertice_list (vertices)
        vertices = self.sort_vert (vertices, 0, max_x)
        print ("after sort")
        self.dump_vertice_list (vertices)
        vertices = self.bisect (vertices)
        print ("get_vertice.bisect 1")
        self.dump_vertice_list (vertices)
        vertices = self.sort_vert (vertices, 1, max_y)
        vertices = self.bisect (vertices)
        print ("get_vertice.bisect 2")
        self.dump_vertice_list (vertices)
        vertices = self.sort_vert (vertices, 2, max_z)
        vertices = self.bisect (vertices)
        print ("get_vertice.bisect 3")
        self.dump_vertice_list (vertices)
        print ("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        print ("end of get_vertice", vertices)
        assert (len (vertices) == 1)
        print ("end of get_vertice returning", vertices[0])
        return vertices[0]
    def find_vert (self, label):
        if label == 'a':
            return self.get_vertice (self._vertices,
                                     False, False, False)
        if label == 'b':
            return self.get_vertice (self._vertices,
                                     True, False, False)
        if label == 'c':
            return self.get_vertice (self._vertices,
                                     True, False, True)
        if label == 'd':
            return self.get_vertice (self._vertices,
                                     False, False, True)
        if label == 'e':
            return self.get_vertice (self._vertices,
                                     True, True, True)
        if label == 'f':
            return self.get_vertice (self._vertices,
                                     False, True, True)
        if label == 'g':
            return self.get_vertice (self._vertices,
                                     False, True, False)
        if label == 'h':
            return self.get_vertice (self._vertices,
                                     True, True, False)
    def dump_vertices (self):
        self.dump_vertice_list (self._vertices)
    def dump_vertice_list (self, vl):
        for i, vert in enumerate (vl):
            print (i, "vert =", vert)
    def sort_vertices (self):
        print ("sort_vert before")
        self.dump_vertices ()
        new_list = []
        print (self.vertice_list ())
        for label in self.vertice_list ():
            print (label)
            new_list += [self.find_vert (label)]
        print ("sort_vertices new_list =")
        self.dump_vertice_list (new_list)
        self._vertices = new_list
        print ("sorted vert complete")
        self.dump_vertices ()
        return self
    def __str__ (self):
        s = "poly ("
        for vert in self._vertices:
            s += str (vert)
            s += ", "
        s = s[:-2]
        s += ")"
        return s
    def length (self):
        return len (self._vertices)
    def sanity_check (self):
        self.dump_vertices ()
        for i, ivec in enumerate (self._vertices):
            for j, jvec in enumerate (self._vertices):
                if (i != j) and (ivec == jvec):
                    print ("inconsistent poly vertices at index", i, "and", j, "both the same", ivec)
                    quit (1)
    def get_vertices (self, label_list = None):
        self.sanity_check ()
        result = []
        if label_list == None:
            for vert in self._vertices:
                assert (vert.is_vec ())
                print (vert)
                print (vert.to_list ())
                result += [vert.to_list ()]
            print ("get_vertices =", result)
            return result
        for label in label_list:
            if len (label) == 1:
                result += [self._vertices[self._labels[label]].to_list ()]
            else:
                for vert in self._faces[self._labels[label]]:
                    result += [self._vertices[vert].to_list ()]
        return result
    def get_vertex (self, name):
        self.sanity_check ()
        return self._vertices[self._labels[name]]
    def get_faces (self):
        return self._faces
    def set_vertices (self, name_dict):
        new_list = []
        for label in self.vertice_list ():
            if label in name_dict:
                new_list += [name_dict[label].dup ()]
            else:
                error ("no label %s found in name_dict\n", label)
        self._vertices = new_list
        self.sanity_check ()
        return self
    #
    #  set_texture for the polygon using label and texture strings.
    #
    def set_texture (self, label, texture):
        if label == 'all':
            self._textures = [texture] * 6
        elif label in self._labels:
            i = self._labels[label]
            self._textures[i] = texture
        else:
            error ("polygon does not have label: %s\n", label)
        return self
    def get_texture (self, label):
        if label in self._labels:
            i = self._labels[label]
            return self._textures[i]
        else:
            error ("polygon does not have label: %s\n", label)
        return self
    #
    #  rotate polygon about the x axis angle degrees.
    #
    def rotate_x (self, angle):
        self.sanity_check ()
        rotation_mat = mat (4).rotate_x (angle)
        print (rotation_mat)
        new_vertices = []
        for vert in self._vertices:
            print (vert)
            new_vertices += [vert.mult_mat (rotation_mat)]
        self._vertices = new_vertices
        return self
    #
    #  rotate polygon about the y axis angle degrees.
    #
    def rotate_y (self, angle):
        self.sanity_check ()
        rotation_mat = mat (4).rotate_y (angle)
        new_vertices = []
        for vert in self._vertices:
            new_vertices += [vert.mult_mat (rotation_mat)]
        self._vertices = new_vertices
        return self
    #
    #  rotate polygon about the z axis angle degrees.
    #
    def rotate_z (self, angle):
        self.sanity_check ()
        rotation_mat = mat (4).rotate_z (angle)
        new_vertices = []
        for vert in self._vertices:
            new_vertices += [vert.mult_mat (rotation_mat)]
        self._vertices = new_vertices
        return self
    #
    #  scale the polygon across the dimensions vec.
    #
    def scale (self, vec):
        self.sanity_check ()
        assert (vec.is_vec ())
        print (vec)
        new_vertices = []
        for vert in self._vertices:
            print ("vert =", vert)
            assert (vert.is_vec ())
            new_vertices += [vert.mult_vec (vec)]
        self._vertices = new_vertices
        return self
    #
    #  translate move the polygon by vec.
    #
    def translate (self, vec):
        print ("poly.translate")
        self.sanity_check ()
        assert (vec.is_vec ())
        print ("prior to translate old_vertices =")
        for vert in self._vertices:
            print (vert)
            assert (vert.is_vec ())
            print ("vert =", vert)
        print ("poly.translate", vec)
        translation_mat = mat (4).translate (vec)
        print ("translate vec =", vec)
        print ("translation_mat =", translation_mat)
        print ("old_vertices =")
        for vert in self._vertices:
            print (vert)
            assert (vert.is_vec ())
            print ("vert =", vert)
        new_vertices = []
        for vert in self._vertices:
            assert (vert.is_vec ())
            print ("vert =", vert)
            tvec = vert.mult_mat (translation_mat)
            print ("translated vec =", tvec)
            new_vertices += [tvec]
        self._vertices = new_vertices
        print ("new_vertices =", new_vertices)
        for vert in self._vertices:
            assert (vert.is_vec ())
            print ("vert =", vert)
        self.sanity_check ()
        return self
    #
    #  reflect_x reflect polygon in the x axis.
    #
    def reflect_x (self):
        self.sanity_check ()
        reflection_mat = mat (4).reflect_x ()
        new_vertices = []
        for vert in self._vertices:
            new_vertices += [reflection_mat.mult_vec (vert)]
        self._vertices = new_vertices
        return self
    #
    #  reflect_y reflect polygon in the x axis.
    #
    def reflect_y (self):
        self.sanity_check ()
        reflection_mat = mat (4).reflect_y ()
        new_vertices = []
        for vert in self._vertices:
            new_vertices += [reflection_mat.mult_vec (vert)]
        self._vertices = new_vertices
        return self
    #
    #  reflect_z reflect polygon in the x axis.
    #
    def reflect_z (self):
        self.sanity_check ()
        reflection_mat = mat (4).reflect_z ()
        new_vertices = []
        for vert in self._vertices:
            new_vertices += [reflection_mat.mult_vec (vert)]
        self._vertices = new_vertices
        return self
    #
    #  mult - multiply each vertice using transform matric mat.
    #
    def mult (self, mat):
        self.sanity_check ()
        assert (mat.is_matrice ())
        new_vertices = []
        for vert in self._vertices:
            vert.extend (4, 1.0)
            print (vert)
            print (mat)
            new_vertices += [vert.mult_mat (mat)]
        self._vertices = new_vertices
        return self
    def __eq__ (self, other):
        self.sanity_check ()
        if self.length () != other.length ():
            return False
        for svec, ovec in zip (self._vertices, other._vertices):
            if svec != ovec:
                return False
        return True
    def __ne__(self, other):
        self.sanity_check ()
        if self.length () != other.length ():
            return True
        for svec, ovec in zip (self._vertices, other._vertices):
            if svec != ovec:
                return True
        return False


#
#
#

def unit_tests ():
    a = poly ().unit_cube ()
    b = poly ().unit_cube ()
    assert (a == b)
    a = vec (1, 0, 1)
    b = vec (1, 0, 1)
    assert (a == b)
    a = vec (1, 0, 1)
    b = vec (1, 0, 0)
    assert (a != b)
    a = vec (1, 2, 3)
    a = a.scale (2)
    assert (a == vec (2, 4, 6))
    a = vec (1, 2, 3)
    b = vec (2, 2, 2)
    assert (a.mult_vec (b) == a.mult_vec (b))
    print ("a.mult_vec (b) =", a.mult_vec (b))
    print ("b.mult_vec (a) =", b.mult_vec (a))
    assert (a.mult_vec (b) == b.mult_vec (a))
    result = a.mult_vec (b)
    print ("result =", result, "a =", a)
    print ("a.mult_vec (b) =", a.mult_vec (b))
    assert (a.mult_vec (b) == vec (2, 4, 6))
    box = poly ().unit_cube ()


if __name__ == "__main__":
    unit_tests ()
