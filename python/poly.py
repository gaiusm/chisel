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



class mat:
    def __init__ (self, dim):
        self._element = []
        self._dim = dim
        self.zeros ()
    def identity (self):
        self._element = []
        self.zeros ()
        for row in range (self._dim):
            self.set_element (row, row, 1)  # set diagonal to 1
    def get_element (self, col, row):
        pos = self._dim * row + col
        return self._element[pos]
    def _set_array (self, pos, value):
        if pos < self._dim:
            if pos == len (self._element) -1:
                self._element = self._element[0:-1]
                self._element += [value]
            elif pos == 0:
                self._element = self._element[1:]
                self._element = [value] + self._element
            else:
                before = self._element[0:pos]
                after = self._element[pos+1:]
                self._element = before + [value] + after
        else:
            error ("_set_array: attempting to set an element outside the matrix dimension")
    def set_element (self, col, row, value):
        pos = self._dim * row + col
        self._set_array (pos, value)
    def _mult_vec (self, vec):
        for row in range (self._dim):
            for col in range (self._dim):
                self.set_element (col, row, get_element (col, row) * vec[row])
        return self
    def _mult_mat (self, m):
        result = mat (self._dim)
        for row in range (self._dim):
            for col in range (self._dim):
                temp = 0
                for d in range (self._dim):
                    temp += get_element (d, row) * m.get_element (col, d)
                result.set_element (col, row, temp)
        self._element = result._element
        return self
    def mult (self, m):
        if len (m) == self._dim:
            # matrix * vector
            return self._mult_vec (m)
        elif len (m) == self._dim * self._dim:
            # matrix * matrix
            return self._mult_mat (m)
        else:
            error ("mat.mult: matrix has %d dimensions and the parameter has: %d elements\n",
                   self._dim, len (m))
    def _add_mat (self, m):
        for row in range (self._dim):
            for col in range (self._dim):
                self.set_element (col, row, self.get_element (col, row) + m.get_element (col, row))
        return self
    def _add_vec (self, vec):
        for row in range (self._dim):
            for col in range (self._dim):
                self.set_element (col, row, self.get_element (col, row) + vec[col])
        return self
    def add (self, m):
        if len (m) == self._dim:
            # matrix + vector
            return self._add_vec (m)
        elif len (m) == self._dim * self._dim:
            # matrix + matrix
            return self._add_mat (m)
        else:
            error ("mat.add: matrix has %d dimensions and the parameter has: %d elements\n",
                   self._dim, len (m))
    def sub (self, m):
        pass
    def translate (self, vec):
        print (vec)
        print ("dim =", self._dim)
        if self._dim == 4:
            if len (vec) < 3:
                error ("translate: vec must contain at least 3 elements")
            radian = self._radian (angle)
            self._elements = [0, 0, 0, vec[0],
                              0, 0, 0, vec[1],
                              0, 0, 0, vec[2],
                              0, 0, 0, 1]
            print ("finishing translate")
            return self
        error ("translate: only dimension 4 understood")
    def _radian (self, degree):
        return Decimal (degree) * Decimal (math.pi) / Decimal (180.0)
    def rotate (self, angle):
        radian = self._radian (angle)
        if self._dim == 2:
            self._elements = [math.cos (radian), math.sin (radian),
                              -math.sin (radian), math.cos (radian)]
        else:
            error ("mat.rotate can only be used when the matrix has two dimensions")
        return self
    def rotate_x (self, angle):
        if self._dim == 2:
            return self.rotate (angle)
        elif self._dim == 3:
            radian = self._radian (angle)
            self._elements = [1, 0, 0,
                              0, math.cos (radian), -math.sin (radian),
                              0, math.sin (radian), math.cos (radian)]
            return self
        elif self._dim == 4:
            radian = self._radian (angle)
            self._elements = [1, 0, 0, 0,
                              0, math.cos (-radian), -math.sin (-radian), 0,
                              0, math.sin (-radian), math.cos (-radian), 0,
                              0, 0, 0, 1]
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
            self._elements = [1, 0, 0, 0,
                              0, math.cos (-radian), math.sin (-radian), 0,
                              0, -math.sin (-radian), math.cos (-radian), 0,
                              0, 0, 0, 1]
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
            self._elements = [math.cos (-radian), -math.sin (-radian), 0, 0,
                              math.sin (-radian), math.cos (-radian), 0, 0,
                              0, 0, 1, 0,
                              0, 0, 0, 1]
            return self
        error ("rotate_x: implementation restriction only dimensions 2, 3 and 4 understood")
    #
    #  scale - returns a matrice which contains a scale for each dimension.
    #
    def scale (self, vec):
        if len (vec) != self._dim:
            error ("mat.scale must have a vector of the same dimension as the matrice")
        else:
            self.zeros ()
            for d in range (self._dim):
                self.set_element (d, d, vec[d])
            return self
    def translate (self, vec):
        self.identity ()
        for d in range (self._dim -1):
            self.set_element (self._dim -1, d, vec[d])
        return self
    def reflect_x (self):
        self.identity ()
        self.set_element (0, 0, -1)
        return self
    def reflect_y (self):
        self.identity ()
        self.set_element (1, 1, -1)
        return self
    def reflect_z (self):
        self.identity ()
        self.set_element (2, 2, -1)
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
#    6+-----+7
#    /|    /|
#  5+-----+4|
#   | |   | |
#   |0+---|-+1
#   |/    |/
#  3+-----+2
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
        self._vertices = [[0, 0, 0],    #  a
                          [0, 1, 0],    #  b  --fixme-- can we switch this with d?
                          [1, 1, 0],    #  c
                          [1, 0, 0],    #  d
                          [1, 1, 1],    #  e
                          [0, 1, 1],    #  f
                          [1, 1, 1],    #  g
                          [1, 0, 1]]    #  h
        return self
    def sort_vertices (self):
        return self
    def get_vertices (self, label_list = None):
        if label_list == None:
            return self._vertices
        result = []
        for label in label_list:
            if len (label) == 1:
                result += [self._vertices[self._labels[label]]]
            else:
                for vert in self._faces[self._labels[label]]:
                    result += [self._vertices[vert]]
        return result
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
        rotation_mat = mat (4).rotate_x (angle)
        new_vertices = []
        for vert in self._vertices:
            new_vertices += [rotation_mat.mult (vert)]
        self._vertices = new_vertices
        return self
    #
    #  rotate polygon about the y axis angle degrees.
    #
    def rotate_y (self, angle):
        rotation_mat = mat (4).rotate_y (angle)
        new_vertices = []
        for vert in self._vertices:
            new_vertices += [rotation_mat.mult (vert)]
        self._vertices = new_vertices
        return self
    #
    #  rotate polygon about the z axis angle degrees.
    #
    def rotate_z (self, angle):
        rotation_mat = mat (4).rotate_z (angle)
        new_vertices = []
        for vert in self._vertices:
            new_vertices += [rotation_mat.mult (vert)]
        self._vertices = new_vertices
        return self
    #
    #  scale the polygon across the dimensions vec.
    #
    def scale (self, vec):
        scale_mat = mat (4).scale (vec)
        new_vertices = []
        for vert in self._vertices:
            new_vertices += [scale_mat.mult (vert)]
        self._vertices = new_vertices
        return self
    #
    #  translate move the polygon by vec.
    #
    def translate (self, vec):
        translation_mat = mat (4).translate (vec)
        new_vertices = []
        for vert in self._vertices:
            new_vertices += [translation_mat.mult (vert)]
        self._vertices = new_vertices
        return self
    #
    #  reflect_x reflect polygon in the x axis.
    #
    def reflect_x (self):
        reflection_mat = mat (4).reflect_x ()
        new_vertices = []
        for vert in self._vertices:
            new_vertices += [reflection_mat.mult (vert)]
        self._vertices = new_vertices
        return self
    #
    #  reflect_y reflect polygon in the x axis.
    #
    def reflect_y (self):
        reflection_mat = mat (4).reflect_y ()
        new_vertices = []
        for vert in self._vertices:
            new_vertices += [reflection_mat.mult (vert)]
        self._vertices = new_vertices
        return self
    #
    #  reflect_z reflect polygon in the x axis.
    #
    def reflect_z (self):
        reflection_mat = mat (4).reflect_z ()
        new_vertices = []
        for vert in self._vertices:
            new_vertices += [reflection_mat.mult (vert)]
        self._vertices = new_vertices
        return self
