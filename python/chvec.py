#!/usr/bin/env python3

# Copyright (C) 2017-2020
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
# Author Gaius Mulley <gaius.mulley@southwales.ac.uk>

from decimal import *
from math import *

#
#  addVec - returns a new list containing the sum of the
#           elements in both indices.
#           It returns a+b of the two vectors.
#

def addVec (pos, vec):
    result = []
    for p, v in zip (pos, vec):
        result += [p+v]
    return result

#
#  subVec - returns a new list containing the subtraction
#           of the elements in both indices.
#           It returns a-b of the two vectors.
#

def subVec (a, b):
    result = []
    for p, v in zip (a, b):
        result += [p-v]
    return result


#
#  minVec - given two lists or vectors, a, b.
#           Return a new list containing the smallest
#           element in either indice or a and b.
#

def minVec (a, b):
    result = []
    for p, v in zip (a, b):
        result += [min (p, v)]
    return result


#
#  maxVec - given two lists or vectors, a, b.
#           Return a new list containing the largest
#           element in either indice or a and b.
#

def maxVec (a, b):
    result = []
    for p, v in zip (a, b):
        result += [max (p, v)]
    return result


#
#  equVec - return true if a == b.
#           We need to test each element of the vector (list).
#

def equVec (a, b):
    for i, j in zip (a, b):
        if i != j:
            return False
    return True

#
#
#

def intVec (v):
    r = []
    for i in v:
        r += [int (i)]
    return r

#
#  crossProduct - return the cross product of a and b.
#                 a x b
#

def crossProduct (a, b):
    assert (len (a) == 3)
    assert (len (b) == 3)
    return [a[1] * b[2] - (b[1] * a[2]),
            a[2] * b[0] - (a[0] * b[2]),
            a[0] * b[1] - (a[1] * b[0])]

#
#  decimalVec - return the vec using Decimal values.
#

def decimalVec (v):
    r = []
    for i in v:
        r += [Decimal ("%g" % i)]
    return r


def sqr (m):
    return m*m

#
#
#

def normaliseVec (v):
    m = 0
    r = []
    for i in v:
        m += sqr (Decimal (i))
    m = sqrt (m)
    for i in v:
        r += [Decimal (i)/ Decimal (m)]
    return r
