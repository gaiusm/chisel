#!/usr/bin/env python

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
# Author Gaius Mulley <gaius@gnu.org>
#

from chvec import *
from sys import exit

debugging = False
expandedCuboids = 0  # how many cuboids have we optimised?
chcuboid_enable_optimise = True


#
#  getexpanded - returns the number of expanded or optimised cuboids.
#

def getexpanded ():
    return expandedCuboids


#
#  setOptimise - turn the optimiser on/off.
#

def setOptimise (on):
    global chcuboid_enable_optimise
    chcuboid_enable_optimise = on


#
#  intersectingRange - returns True if range (a0..a1) intersects with range (b0..b1).
#                      It is easier to test whether they do not intersect
#                      and invert the result.  They do not intersect if a0 lies after b1.
#                      or if the end of a1 is before the start of b0.
#                      It returns True if they touch.
#

def intersectingRange (a0, a1, b0, b1):
    return not ((a0 > b1) or (a1 < b0))

#
#  interpenetrationRange - return True if a0..a1 and b0..b1 overlap.
#                          Crucially this returns False if they touch.
#

def interpenetrationRange (a0, a1, b0, b1):
    return not ((a0 >= b1) or (a1 <= b0))


class cuboid:
    def __init__ (self, pos, size, material, transform, cuboidno, fixed):
        self.pos = pos
        self.size = size
        self.end = addVec (pos, size)
        self.material = material
        self.transform = transform
        self.cuboidno = cuboidno
        self.fixed = fixed
        self.debugging = debugging

    #
    #  interpenetration - return True if self penetrates with the proposed
    #                    cuboid defined by pos, size.
    #

    def interpenetration (self, pos, size):
        return self._interpenetrationAxis (pos, addVec (pos, size))

    #
    #  _interpenetrationAxis - return True if the x, y, and z axis penetrates
    #                          between cuboid self and cuboid bpos/bend.
    #                          bpos is the bottom left position of the cuboid.
    #                          bend is the top right position of the cuboid.
    #

    def _interpenetrationAxis (self, bpos, bend):
        # --complete me--
        # return True if there is an interpenetration on the x axis between
        #             bpos/bend and self
        #        AND  if there is an interpenetration on the y axis between
        #             bpos/bend and self
        #        AND  if there is an interpenetration on the z axis between
        #             bpos/bend and self
        return False

    #
    #  _limits - return True if self has the same start end limits as defined by pos, size
    #            in the dimension, dim.
    #

    def _limits (self, pos, size, dim):
        end = addVec (pos, size)
        return (pos[dim] == self.pos[dim]) and (end[dim] == self.end[dim])

    #
    #  _xlimits - return True if self has the same x start, end as defined by pos and size.
    #

    def _xlimits (self, pos, size):
        # hint look at _limits
        pass # --complete me--

    #
    #  _ylimits - return True if self has the same y start, end as defined by pos and size.
    #

    def _ylimits (self, pos, size):
        # hint look at _limits
        pass # --complete me--

    #
    #  _zlimits - return True if self has the same x start, end as defined by pos and size.
    #

    def _zlimits (self, pos, size):
        # hint look at _limits
        pass # --complete me--

    #
    #  canExtend - returns True if we can enlarge self to contain pos, size.
    #              We can only do this if pos, size joins or overlaps with self.
    #              We have already tested for a superset or subset elsewhere so
    #              this routine just handles extending a cuboid.
    #

    def _canExtend (self, pos, size):
        if chcuboid_enable_optimise:
            #
            #  if the self x and y limits are the same as (pos and size)
            #  then
            #     see if we can extend the z axis to combine the cuboid
            #  do the same for the z, x and y axis
            #  do the same for the z, y and x axis
            #
            pass
        return False  # --complete me--


    #
    #  _enlarge - we know that self can be enlarged to contain, pos, end.
    #             Futhermore we know we are only going to grow one axis.
    #             (the other two axis will be the same).
    #             We also know that the pos, size might fit inside, or
    #             partially fit inside or join exactly to the end or start of self.
    #             So all we need to do is move the self.pos and self.end to
    #             consume pos, end.
    #

    def _enlarge (self, pos, end):
        self.pos = minVec (self.pos, pos)
        self.end = maxVec (self.end, end)
        self.size = subVec (self.end, self.pos)
        if self.debugging:
            print ("_enlarging", self.pos, self.end, self.size)

    #
    #  _extend - return True if self was extended to include cuboid pos, size in the
    #            dimension, dim.  It tests whether it overlaps or whether it just
    #            touches self at either end.
    #

    def _extend (self, pos, size, dim):
        end = addVec (pos, size)
        if (intersectingRange (pos[dim], end[dim], self.pos[dim], self.end[dim]) or
            (pos[dim] == self.end[dim]) or (end[dim] == self.pos[dim])):
            self._enlarge (pos, end)
            return True
        return False

    #
    #  _Xextend - return True if cuboid self was extended along the X axis to
    #             consume pos, size.
    #

    def _Xextend (self, pos, size):
        return self._extend (pos, size, 0)

    #
    #  _Yextend - return True if cuboid self was extended along the Y axis to
    #             consume pos, size.
    #

    def _Yextend (self, pos, size):
        return self._extend (pos, size, 1)

    #
    #  _Zextend - return True if cuboid self was extended along the Z axis to
    #             consume pos, size.
    #

    def _Zextend (self, pos, size):
        return self._extend (pos, size, 2)

    #
    #  _inside - returns True if pos is inside self.
    #

    def _inside (self, pos):
        return ((pos[0] >= self.pos[0]) and (pos[0] <= self.end[0]) and
                (pos[1] >= self.pos[1]) and (pos[1] <= self.end[1]) and
                (pos[2] >= self.pos[2]) and (pos[2] <= self.end[2]))

    #
    #  subset - returns True if cuboid of pos, size
    #           will fit inside self.
    #

    def subset (self, pos, size):
        return self._inside (pos) and self._inside (addVec (pos, size))

    #
    #  _superset - return True if cuboid, pos, size will contain self.
    #

    def _superset (self, pos, size):
        b = cuboid (pos, size, None, None, None, None)
        return b.subset (self.pos, self.size)

    #
    #  combined - return if we have managed to combine self
    #             with a proposed new cubiod as defined by
    #             pos, size and material.  The material must
    #             be the same.  The arguments pos and size are
    #             might be inside (in which case we return True
    #             and do nothing) or are a superset of self
    #             in which case we change self to be the larger
    #             cuboid and return True.  Finally it
    #             tries to extend self to consume pos, size
    #             by first testing whether pos, size fit on
    #             the end of self (it tries to grow self with
    #             no gaps to consume, pos, size).  If successful
    #             it returns True.
    #

    def combined (self, pos, size, material, transform, fixed):
        global expandedCuboids
        if self.samekind (material, transform, fixed):
            if self.subset (pos, size):
                expandedCuboids += 1
                return True
            if self._superset (pos, size):
                self.pos = pos
                self.size = size
                self.end = addVec (pos, size)
                expandedCuboids += 1
                return True
            if self._canExtend (pos, size):
                expandedCuboids += 1
                return True
        if self.debugging:
            print(pos, size, "does not fit onto", self.pos, self.size)
        return False

    def samekind (self, material, transform, fixed):
        return ((material == self.material) and
                (transform == self.transform) and
                (fixed == self.fixed))


def regressionTest ():
    global expandedCuboids

    errors = 0
    print("regression tests for chcuboid")
    pos = [1, 1, 1]
    size = [1, 1, 1]
    b = cuboid (pos, size, "wall", 0)
    for i in range (1, 10):
        pos = [i, 1, 1]
        if b.combined (pos, size, "wall", "wall", True):
            print("pass x growth", end=' ')
            print("pos =", pos, "size =", size, end=' ')
            print("will be combined into existing brick")
        else:
            print("error x growth", end=' ')
            print("pos =", pos, "size =", size, "is not combined into existing brick")
            errors = 1
    pos = [1, 1, 1]
    size = [1, 1, 1]
    b = cuboid (pos, size, "wall", 0)
    for j in range (1, 10):
        pos = [1, j, 1]
        if b.combined (pos, size, "wall", "wall", True):
            print("pass y growth", end=' ')
            print("pos =", pos, "size =", size, end=' ')
            print("will be combined into existing brick")
        else:
            print("error y growth", end=' ')
            print("pos =", pos, "size =", size, "is not combined into existing brick")
            errors = 2
    pos = [1, 1, 1]
    size = [1, 1, 1]
    b = cuboid (pos, size, "wall", 0)
    for k in range (1, 10):
        pos = [1, 1, k]
        if b.combined (pos, size, "wall", "wall", True):
            print("pass z growth", end=' ')
            print("pos =", pos, "size =", size, end=' ')
            print("will be combined into existing brick")
        else:
            print("error z growth", end=' ')
            print("pos =", pos, "size =", size, "is not combined into existing brick")
            errors = 3
    if errors != 0:
        print("regression test errors, exiting")
        exit (errors)
    expandedCuboids = 0


if __name__ == "__main__":
    setOptimise (True)
    if chcuboid_enable_optimise:
        print("optimisation set, running the regression tests")
        regressionTest ()
