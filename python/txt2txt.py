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
#

import getopt, sys, string

inputFile = None
defines = {}
verbose = False
debugging = False
floor = []
rooms = {}
maxx, maxy = 0, 0
doorValue, wallValue, emptyValue = 0, -1, -2
versionNumber = 0.1


def mycut (l, i):
    if i == 0:
        if len (l) > 1:
            return None, l[i], l[i+1:]
        return None, l[i], None
    if len (l) > i+1:
        return l[:i], l[i], l[i+1:]
    return l[:i], l[i], None


def mystitch (a, b, c):
    if a == None:
        d = b
    else:
        d = a + b
    if c == None:
        return d
    return d + c


def setFloor (x, y, value):
    global floor
    a, b, c = mycut (floor, y)
    x, y, z = mycut (b, x)
    b = mystitch (x, [value], z)
    floor = mystitch (a, [b], c)


def getFloor (x, y):
    global floor
    return floor[y][x]


def initFloor (x, y, value):
    global floor
    floor = []
    for j in range (y+1):
        row = [value] * (x+1)
        floor += [row]


class roomInfo:
    def __init__ (self, w, d):
        self.walls = w
        self.doors = d
        self.doorLeadsTo = []
        self.monsters = []
        self.weapons = []
        self.ammo = []
        self.lights = []
        self.worldspawn = []


#
#  printf - keeps C programmers happy :-)
#

def printf (format, *args):
    print(str(format) % args, end=' ')


#
#  error - issues an error message and exits.
#

def error (format, *args):
    print(str (format) % args, end=' ')
    sys.exit (1)


#
#  debugf - issues prints if debugging is set
#

def debugf (format, *args):
    global debugging
    if debugging:
        print(str (format) % args, end=' ')


def usage (code):
    print("Usage: txt2pen [-dhvV] [-o outputfile] inputfile")
    print("  -d debugging")
    print("  -h help")
    print("  -V verbose")
    print("  -v version")
    print("  -o outputfile name")
    sys.exit (code)


#
#  handleOptions -
#

def handleOptions ():
    global debugging, verbose, outputName

    outputName = None
    try:
       optlist, l = getopt.getopt(sys.argv[1:], ':dho:vV')
       for opt in optlist:
           if opt[0] == '-d':
               debugging = True
           elif opt[0] == '-h':
               usage (0)
           elif opt[0] == '-o':
               outputName = opt[1]
           elif opt[0] == '-v':
               printf ("txtpen version " + str (versionNumber) + "\n")
               sys.exit (0)
           elif opt[0] == '-V':
               verbose = True
       if l != []:
           return (l[0], outputName)

    except getopt.GetoptError:
       usage (1)
    return (None, outputName)


def errorLine (n, line, text):
    global inputFile
    full = "%s:%d:%s\n%s:%d:%s\n" % (inputFile, n, text, inputFile, n, line)
    sys.stderr (full)


def addDef (c, line, l):
    global defines
    a = c[0]
    if len (c) > 1:
        c = c[1:]
        c = c.lstrip ()
        defines[a] = c
    else:
        errorLine (l, line, 'define must have a full definition')


#
#  isSubstr - safely test whether the start of string, s, is, c.
#             return True if this is the case.  s can be any length.
#

def isSubstr (s, c):
    return (len (s) > len (c)) and (s[:len(c)] == c)


def readDefines (i):
    l = 1
    for line in i:

        c = line.lstrip ()
        if isSubstr (c, 'define'):
            c = c[len ('define'):]
            c = c.lstrip ()
            addDef (c, line, l)
        l += 1
    return i


#
#  readMap - read in the map component of the txt file
#

def readMap (i):
    mapGrid = []
    inMap = False
    s = 0
    for line in i:
        s += 1
        c = line.lstrip ()
        if (len (c) > 0) and (c[0] == '#'):
            inMap = True
        if inMap:
            mapGrid += [c]
    return mapGrid, s


#
#  getListOfRooms - returns the number of rooms declared.
#

def getListOfRooms (mapGrid, start, i):
    global defines
    listOfRooms = []
    pos = []
    for y, r in enumerate (mapGrid, start=1):
        for x, c in enumerate (r, start=1):
            if c in defines:
                k = defines[c]
                if isSubstr (k, 'room'):
                    pos += [[x, y]]
                    k = k.split ()[1:]
                    k = string.join (k)
                    k = k.split ()[0]
                    listOfRooms += [k]
    return listOfRooms, pos


def isWall (pos, grid):
    return grid[pos[1]][pos[0]] == '#'


def isDoor (pos, grid):
    return (grid[pos[1]][pos[0]] == '-') or (grid[pos[1]][pos[0]] == '|') or (grid[pos[1]][pos[0]] == '.')


def isPlane (pos, grid):
    return isWall (pos, grid) or isDoor (pos, grid)


def addVec (pos, vec):
    return [pos[0]+vec[0], pos[1]+vec[1]]


def moveBy (pos, vec, grid):
    if vec[0] != 0:
        while not isPlane (addVec (pos, [vec[0], 0]), grid):
            pos = addVec (pos, [vec[0], 0])
    if vec[1] != 0:
        while not isPlane (addVec (pos, [0, vec[1]]), grid):
            pos = addVec (pos, [0, vec[1]])
    return pos


def addWall (walls, start, end):
    if start != end:
        walls += [[start, end]]
        return walls, end
    return walls, start


def lookingLeft (pos, left, grid, s):
    if debugging:
        print(pos, left, s)
    if s[1] == ' ' and isPlane (pos, grid):
        return False
    if s[1] == 'x' and (not isPlane (pos, grid)):
        return False
    if s[1] == '.' and (not isDoor (pos, grid)):
        if debugging:
            print("no door at", pos)
        return False
    if s[0] == ' ' and isPlane (addVec (pos, left), grid):
        return False
    if s[0] == 'x' and (not isPlane (addVec (pos, left), grid)):
        return False
    if s[0] == '.' and (not isDoor (addVec (pos, left), grid)):
        return False
    return True

def mystop ():
    pass

def scanRoom (topleft, p, mapGrid, walls, doors):
    global debuging
    s = p
    a = addVec (p, [-1, -1])
    d = 1  # 0 up, 1 right, 2 down, 3 left
    leftVec = [[-1, 0], [0, -1], [1, 0], [0, 1]]
    forwardVec = [[0, -1], [1, 0], [0, 1], [-1, 0]]
    if debugging:
        print("wall corner", p)

    doorStartPoint = None
    doorEndPoint = None
    while True:
        if debugging:
            print("point currently at", p, d)
        if (doorStartPoint == None) and lookingLeft (p, leftVec[d], mapGrid, '. '):
            if debugging:
                print("seen first point", p)
            # first point on the wall is a door
            doorStartPoint = addVec (p, leftVec[d])
            doorEndPoint = doorStartPoint
        if lookingLeft (addVec (p, forwardVec[d]), leftVec[d], mapGrid, '. '):
            if debugging:
                print("seen a door point", p, end=' ')
            if doorStartPoint == None:
                doorStartPoint = addVec (addVec (p, forwardVec[d]), leftVec[d])
            doorEndPoint = addVec (addVec (p, forwardVec[d]), leftVec[d])
        else:
            # end of door?
            if doorEndPoint != None:
                doors += [[doorStartPoint, doorEndPoint]]
                doorStartPoint = None
                doorEndPoint = None
        if lookingLeft (addVec (p, forwardVec[d]), leftVec[d], mapGrid, 'x '):
            # carry on
            p = addVec (p, forwardVec[d])
        elif lookingLeft (addVec (p, forwardVec[d]), leftVec[d], mapGrid, 'x.'):
            if debugging:
                print("wall corner (x.)", p)
            walls, a = addWall (walls, a, addVec (addVec (p, forwardVec[d]), leftVec[d]))
            # end of door?
            if doorEndPoint != None:
                doors += [[doorStartPoint, doorEndPoint]]
            doorStartPoint = None
            doorEndPoint = None
            # turn right
            d = (d + 1) % 4
            if s == p:
                # back to the start
                return walls, doors
        elif lookingLeft (addVec (p, forwardVec[d]), leftVec[d], mapGrid, 'xx'):
            if debugging:
                print("wall corner (xx)", p)
            walls, a = addWall (walls, a, addVec (addVec (p, forwardVec[d]), leftVec[d]))
            # end of door?
            if doorEndPoint != None:
                doors += [[doorStartPoint, doorEndPoint]]
            doorStartPoint = None
            doorEndPoint = None
            # turn right
            d = (d + 1) % 4
            if s == p:
                # back to the start
                return walls, doors
        elif lookingLeft (addVec (p, forwardVec[d]), leftVec[d], mapGrid, '  '):
            if debugging:
                print("wall corner (  )", p, end=' ')
            # walls, a = addWall (walls, a, addVec (addVec (p, forwardVec[d]), leftVec[d]))
            walls, a = addWall (walls, a, addVec (p, leftVec[d]))
            if debugging:
                print("at point", a)
            # turn left
            p = addVec (p, forwardVec[d])
            d = (d + 3) % 4
            if s == p:
                # back to the start
                return walls, doors
        else:
            printf ("something went wrong here\n")


def printCoord (c, o):
    global maxy
    o.write (str (c[0]+1) + " " + str ((maxy-c[1])+1))
    return o


def printMonsters (mlist, o):
    if mlist != []:
        for kind, pos in mlist:
            o.write ("   MONSTER " + kind + " AT ")
            printCoord (pos, o)
            o.write ("\n")
    return o


def printSpawnPlayer (m, o):
    if m != []:
        for pos in m:
            o.write ("   SPAWN PLAYER AT ")
            printCoord (pos, o)
            o.write ("\n")
    return o


def printAmmo (m, o):
    if m != []:
        for name, amount, pos in m:
            o.write ("   AMMO " + name + " AMOUNT " + amount + " AT ")
            printCoord (pos, o)
            o.write ("\n")
    return o


def printWeapons (w, o):
    if w != []:
        for name, pos in w:
            o.write ("   WEAPON " + name + " AT ")
            printCoord (pos, o)
            o.write ("\n")
    return o


def printLights (l, o):
    if l != []:
        for pos in l:
            o.write ("   LIGHT AT ")
            printCoord (pos, o)
            o.write ("\n")
    return o


def printRoom (r, o):
    o.write ("ROOM " + str (r) + "\n")
    o.write ("   WALL\n")
    for p in rooms[r].walls:
        o.write ("   ")
        for c in p:
            o.write ("  ")
            printCoord (c, o)
        o.write ("\n")
    for i, d in enumerate (rooms[r].doors):
        o.write ("   DOOR ")
        for c in d:
            printCoord (c, o)
            o.write (" ")
        o.write ("STATUS OPEN LEADS TO " + str (rooms[r].doorLeadsTo[i]) + "\n")
    o = printMonsters (rooms[r].monsters, o)
    o = printAmmo (rooms[r].ammo, o)
    o = printWeapons (rooms[r].weapons, o)
    o = printLights (rooms[r].lights, o)
    o = printSpawnPlayer (rooms[r].worldspawn, o)
    o.write ("END\n\n")
    return o


def generateRoom (r, p, mapGrid, start, i):
    global verbose, rooms, debugging

    if verbose:
        print("room", r, end=' ')
    p = moveBy (p, [-1, -1], mapGrid)
    if verbose:
        print("top left is", p)
    s = p
    walls, doors = scanRoom (s, p, mapGrid, [], [])
    if debugging:
        print(walls)
    rooms[r] = roomInfo (walls, doors)


def plot (w, value):
    x0 = min (w[0][0], w[1][0])
    x1 = max (w[0][0], w[1][0])
    y0 = min (w[0][1], w[1][1])
    y1 = max (w[0][1], w[1][1])
    if x0 == x1:
        for j in range (y0, y1+1):
            setFloor (x0, j, value)
    else:
        for i in range (x0, x1+1):
            setFloor (i, y0, value)


def onFloor (r):
    global verbose, rooms, maxx, maxy, wallValue, doorValue

    for w in rooms[r].walls:
        plot (w, wallValue)
    for d in rooms[r].doors:
        plot (d, doorValue)


def findMax (r):
    global rooms, maxx, maxy
    for w in rooms[r].walls:
        for c in w:
            maxx = max (c[0], maxx)
            maxy = max (c[1], maxy)


def dumpFloor ():
    print("the map")
    for r in floor:
        for c in r:
            if c == emptyValue:
                print(" ", end=' ')
            elif c == doorValue:
                print(".", end=' ')
            elif c == wallValue:
                print("#", end=' ')
            else:
                print(str (c), end=' ')
        print(" ")
    print(" ")


def floodFloor (r, p):
    if p[0] >= 0 and p[1] >= 0:
        if getFloor (p[0], p[1]) == emptyValue:
            setFloor (p[0], p[1], r)
            floodFloor (r, [p[0]-1, p[1]])
            floodFloor (r, [p[0]+1, p[1]])
            floodFloor (r, [p[0], p[1]-1])
            floodFloor (r, [p[0], p[1]+1])


def floodRoom (r, p):
    floodFloor (int (r), p)


#
#  isVertical - return True if, c, is a vertical line.
#

def isVertical (c):
    return c[0][0] == c[1][0]

#
#  isHorizontal - return True if, c, is a horizontal line.
#

def isHorizontal (c):
    return c[0][1] == c[1][1]


#
#  isUpon - returns true if line, d, is upon, w.
#

def isUpon (d, w):
    if isVertical (w):
        if w[0][0] != d[0][0]:
            return False
        d0 = min (d[0][1], d[1][1])
        d1 = max (d[0][1], d[1][1])
        w0 = min (w[0][1], w[1][1])
        w1 = max (w[0][1], w[1][1])
    else:
        if w[0][1] != d[0][1]:
            return False
        d0 = min (d[0][0], d[1][0])
        d1 = max (d[0][0], d[1][0])
        w0 = min (w[0][0], w[1][0])
        w1 = max (w[0][0], w[1][0])
    return (d0 > w0) and (d1 < w1)


#
#  findWall - return the wall which door, d, is upon.
#

def findWall (r, d):
    for w in rooms[r].walls:
        if isUpon (d, w):
            return w

def findDoors (r, p):
    for d in rooms[r].doors:
        w = findWall (r, d)
        if isVertical (w):
            # vertical door as it is on a vertical wall
            if getFloor (d[0][0]+1, d[0][1]) != int (r):
                rooms[r].doorLeadsTo += [getFloor (d[0][0]+1, d[0][1])]
            else:
                rooms[r].doorLeadsTo += [getFloor (d[0][0]-1, d[0][1])]
        else:
            # horizontal door as it is on a horizontal wall
            if getFloor (d[0][0], d[0][1]+1) != int (r):
                rooms[r].doorLeadsTo += [getFloor (d[0][0], d[0][1]+1)]
            else:
                rooms[r].doorLeadsTo += [getFloor (d[0][0], d[0][1]-1)]


def findEntities (g, room, p):
    if debugging:
        for l in g:
            print(l, end=' ')
        for l in floor:
            print(l)
    for y, r in enumerate (g):
        for x in range (maxx+1):
            if getFloor (x, y) == int (room):
                c = r[x]
                if c in defines:
                    if debugging:
                        print("seen", c, "at", x, y)
                    k = defines[c]
                    if isSubstr (k, 'worldspawn'):
                        rooms[room].worldspawn += [[x, y]]
                    elif isSubstr (k, 'light'):
                        rooms[room].lights += [[x, y]]
                    elif isSubstr (k, 'monster'):
                        words = k.split ()
                        if len (words) > 1:
                            name = words[1]
                            rooms[room].monsters += [[name, [x, y]]]
                        else:
                            error ('expecting a name after they keyword monster')
                    elif isSubstr (k, 'ammo'):
                        words = k.split ()
                        if len (words) > 2:
                            rooms[room].ammo += [[words[1], words[2], [x, y]]]
                        else:
                            error ('expecting a number and quantity after the keyword ammo')
                    elif isSubstr (k, 'weapon'):
                        words = k.split ()
                        if len (words) > 1:
                            rooms[room].weapons += [[words[1], [x, y]]]
                        else:
                            error ('expecting a number and quantity after the keyword ammo')


#
#  generatePen - generate penguin tower map from, mapGrid.
#                start is the line number in file, i, where
#                the map grid commences.  o is the outputfile.
#

def generatePen (mapGrid, start, i, o):
    global maxx, maxy
    listOfRooms, pos = getListOfRooms (mapGrid, start, i)
    if listOfRooms == []:
        errorLine (start, mapGrid[0], "the map must have at least one room defined")
    else:
        for r, p in zip (listOfRooms, pos):
            generateRoom (r, p, mapGrid, start, i)
        for r in listOfRooms:
            findMax (r)
        initFloor (maxx, maxy, emptyValue)
        for r in listOfRooms:
            onFloor (r)
        for r, p in zip (listOfRooms, pos):
            floodRoom (r, p)
        for r, p in zip (listOfRooms, pos):
            findDoors (r, p)
        for r, p in zip (listOfRooms, pos):
            findEntities (mapGrid, r, p)
        for r in listOfRooms:
            o = printRoom (r, o)
        o.write ("END.\n")
    return o


#
#  processMap
#

def processMap (i, o):
    i = readDefines (i)
    g, s = readMap (i)
    generatePen (g, s, i, o)
    return o


#
#  main - handle the input/output file options and call processMap.
#

def main ():
    global inputFile
    io = handleOptions ()
    if io[0] == None:
        # input file not set so use stdin
        inputFile = 'stdin'
        i = sys.stdin
    else:
        inputFile = io[0]
        i = open (io[0], 'r')
    if io[1] == None:
        # output file not set so use stdout
        o = sys.stdout
    else:
        o = open (io[1], 'w')
    o = processMap (i.readlines (), o)
    o.flush ()


main ()
