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

from decimal import *
from math import *
from poly import *




#
#  staircase
#

def staircase (room, pos, height, r0, r1, increment, angle):
    floor_level = get_floor_level (room)
    stair_level_offset = 0
    stair_angle = 0
    while stair_level_offset < height:
        newstair (room, pos, r0, r1, increment,
                  angle, stair_angle, stair_level_offset)
        stair_angle += angle
        stair_level_offset += increment
