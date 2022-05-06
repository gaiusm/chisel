#!/usr/bin/env python3

# Copyright (C) 2022
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
#

import sys, pen2map

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
    # sys.exit (1)


class polymap:
    def __init__ (self):
        self.poly_brick = {}
        self.poly_brickno = 0
    def add_polybrick (self, brick):
        self.poly_brickno += 1
        self.poly_brick[self.poly_brickno] = [brick]
    #
    #  flush - flush all the poly brushdef3 based objects.
    #
    def write (outputFile, brushdef3count):
        for key in list (self.poly_brick.keys ()):
            brick = self.poly_brick[key]  # Python v2 and v3 compatible
            if debugging:
                printf ("poly_brick: %d\n", key)
            outputFile.write ('    // poly_brick ' + str (key) + '\n')
            outputFile.write ('    {\n')
            outputFile.write ('         brushDef3\n')
            outputFile.write ('         {\n')
            outputFile = self._write_brick (outputFile, brick)
            outputFile.write ('         }\n')
            outputFile.write ('    }\n')
            brushdef3count += 1
        return outputFile, brushdef3count
    #
    #
    #
    def _write_brick (self, outputFile, brick):
        pen2map.polybrick (outputFile,
                           brick.get_vertices (),
                           brick.get_faces (),
                           brick.get_texture ("top"),
                           brick.get_texture ("top"))
