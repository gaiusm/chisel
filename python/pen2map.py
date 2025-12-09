#!/usr/bin/env python3

# Copyright (C) 2017-2023
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

import argparse, sys, string
from chvec import *
from chcuboid import *
import math, random
from poly import poly, vec, unit_tests, mat


"""
EBNF of the pen file format

FileUnit := RoomDesc { RoomDesc } "END." =:

roomDesc := "ROOM" integer { doorDesc | wallDesc | treasureDesc | ammoDesc |
                            lightDesc | insideDesc | weaponDesc | monsterDesc |
                            spawnDesc | defaultDesc | soundDesc | labelDesc |
                            plinthDesc } =:

soundDesc := "SOUND" "AT" { volumeDesc | loopingDesc | waitDesc } =:

volumeDesc := "VOLUME" integer =:

loopingDesc := "LOOPING" =:

waitDesc := "WAIT" integer =:

defaultDesc := "DEFAULT" defaultConfig =:

defaultColourConfig := "COLOUR" ( "CEILING" | "MID" | "FLOOR" ) int int int =:

defaultTextureConfig := ( "CEILING" | "FLOOR" | "WALL" | "PLINTH" | "BEAM" ) string =:

defaultConfig := "COLOUR" defaultColourConfig |
                 "TEXTURE" defaultTextureConfig =:

spawnDesc := "SPAWN" "PLAYER" "AT" posDesc =:

monsterDesc := 'MONSTER' type 'AT' posDesc =:

weaponDesc := 'LIGHT' 'AT' posDesc =:

insideDesc := 'INSIDE' 'AT' posDesc =:

labelDesc := 'INSIDE' 'AT' posDesc string =:

lightDesc := 'LIGHT' 'AT' posDesc [ 'COLOUR' int int int ] [ 'ON' string ] =:

ammoDesc := "AMMO" integer "AMOUNT" integer "AT" posDesc =:

posDesc := integer integer =:

doorDesc := "DOOR" doorCoords { doorCoords } =:

doorCoords := integer integer integer integer status "LEADS" "TO" integer =:

status := "STATUS" ( [ 'OPEN' | 'CLOSED' | 'SECRET' ] ) =:

WallDesc := 'WALL' WallCoords { WallCoords } =:

PlinthDesc := 'PLINTH int int int =:

WallCoords := Integer Integer Integer Integer =:

"""

defines = {}
debugFloorLevel = False
toTxt, toMap = False, False
ssName = None
floor = []
rooms = {}
brushes = {}
maxx, maxy = 0, 0
doorValue, wallValue, emptyValue = 0, -1, -2
versionNumber = "0.1"
currentLineNo = 1
words = []
curStatus = None
status_open, status_closed, status_secret = list (range (3))
curRoom = None
curRoomNo = None
curPos = None
direction = ["left", "top", "right", "bottom"]
doorStatus = ["open", "closed", "secret"]
maxEntities = 4096    # doom3 limitation
singlePlayer, deathMatch = list(range(2))
maxd3Units = 5000
minx, miny, minz, maxz = None, None, None, None
lightPoints = []
optimise = False
regressionRequired = False
curCol = []
defaultOn = "MID"
curOn = defaultOn
defaultColour = [150, 150, 150]
minFloor, maxFloor = 0, 0
args = None
enableSpiralStairs = True
roomCuboids = True
stepAngleClockwise = 10.0  # Degrees


plinthBase = 4*3 #  inches
plinthTop = 2*3  #  inches
plinthMid = 1*3  #  inch
plinthReduction = 2*3 # inches
plinthReduction2 = 3*3 # inches

archBase       = 12 * 3 # inches
archBaseHeight = 12 * 3 # inches
archTop        = 12 * 3 # inches
archTopHeight  = 2*3 # inches
archMidHeight  = 1*3 # inches
archReduction  = 10 * 3 # inches
archReduction2 =  8 * 3 # inches

archBlockAngle = 15     # degrees
archCapAngle   = 20     # degrees
archBaseAngle  = 20     # degrees
archBlockBase  = 12 * 4 # inches
archSegmentBase= 9  * 4 # inches

defaults = { "portal":"textures/editor/visportal",
             "open":"textures/editor/visportal",
             "closed":"textures/hell/wood1",
             "secret":"secret",
             "wall":"textures/hell/cbrick2",
             "floor":"textures/hell/qfloor",
             "ceiling":"textures/hell/wood1",
             "beam"   :"textures/hell/wood1",
             "brick" : "textures/caves/sbricks2",
             "open_transform"   :"( ( 0.0078125 0 0 ) ( 0 0.0078125 1.5 ) )",
             # portal transform is a no-op but it allows code reuse.
             "portal_transform" :"( ( 0.0078125 0 0 ) ( 0 0.0078125 1.5 ) )",
             "wall_transform"   :"( ( 0.0078125 0 0.5 ) ( 0 -0.0078125 -1 ) )",
             ##### "wall_transform"   :"( ( 0.0156250019 0 1.0000002384 ) ( 0 0.015625 6.25 ) )",
             # "floor_transform"  :"( ( 0.03 0 0 ) ( 0 0.03 0 ) )",  # works well for quake1 textures
             "floor_transform"  :"( ( 0.0078125 0 0.5 ) ( 0 -0.0078125 -1 ) )",
             "plinth_transform" :"( ( 0.03 0 0 ) ( 0 0.03 0 ) )",
             "ceiling_transform":"( ( 0.0078125 0 0 ) ( 0 0.0078125 0 ) )",
             "beam_transform"   :"( ( 0.0078125 0 0 ) ( 0 0.0078125 0 ) )",
             "secret_transform" :"( ( 0.0156250019 0 1.0000002384 ) ( 0 0.015625 6.25 ) )",
             "brick_transform"  :"( ( 0.015625 0 0 ) ( 0 0.0078125 0 ) )" }
secretDoorLintal = "wall"

scopeStack = [defaults]


#
# units are in inches, it doesn't make sense having metric castles!
# the doom3 game engine units are also in inches.
#

doorThickness      = 3                # number of inches thick for the lintel and posts of a door
inchesPerUnit      = 48               # one ascii position represents this number of inches (4 feet)
halfUnit           = inchesPerUnit/2
wallThickness      = halfUnit         # number of inches thick for a brick

#
# the remaining contants are in inchesPerUnit
#

beamSupportSize    = 0.5       # 2 foot beam support
lintelThickness    = 0.5       # 2 foot lintel over the door
minCeilingHeight   = 6         # 6x48 inches minimum
minDoorHeight      = minCeilingHeight-lintelThickness   #
candleHeight       = minCeilingHeight-1   # 5x48 inches for a candle above the beam
spawnHeight        = 0.5       # players spawn 2 feet off the floor
invSpawnHeight     = 0.25      # 1 foot off the floor
lightBlock         = 0.25      # 1 foot block
lightHeight        = 1.25      # 5 foot high
lightBlockHeight   = 1.0       # 4 foot high
lightFloorHeight   = 0.0625    # 3 inches
lightFloorHeight   = 0.125     # 6 inches
lightFloorHeight   = 0.25      # 1 foot
lightFloorHeight   = 0.5       # 2 foot
lightCeilingHeight = minCeilingHeight - 1.5
floorStep          = 0.25      # 1 foot
noSteps            = 4         # how many steps per unit
stairWall          = 0.25      # 1 foot
stairLight         = 0.25      # 1 foot
#
#  the bricks are used to construct secret doors (not ordinary walls)
#
# brickLength        = 0.25      # 1 foot brick
# brickWidth         = 0.08      # 4 inches wide
# brickHeight        = 0.0625    # 3 inches height
# brickMidOffset     = 0.5 - brickWidth/2.0
brickLength        = 0.5      # 1 foot brick
brickWidth         = 0.25      # 4 inches wide
brickHeight        = 0.5    # 3 inches height
brickMidOffset     = 0.25 #  - brickWidth/2.0


class staircase:
    def __init__ (self, x, y, orient, clockwise, up, dest):
        self.x = x
        self.y = y
        self.orient = orient
        self.clockwise = clockwise
        self.up = up
        self.dest = dest


class coke:
    def __init__ (self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


def coke_can (r, x, y, z):
    global rooms
    rooms[r].cokeCans += [coke (x, y, z)]


def cut (l, i):
    if i == 0:
        if len (l) > 1:
            return None, l[i], l[i+1:]
        return None, l[i], None
    if len (l) > i+1:
        return l[:i], l[i], l[i+1:]
    return l[:i], l[i], None


def stitch (a, b, c):
    if a == None:
        d = b
    else:
        d = a + b
    if c == None:
        return d
    return d + c


def setFloor (x, y, value):
    global floor
    a, b, c = cut (floor, y)
    x, y, z = cut (b, x)
    b = stitch (x, [value], z)
    floor = stitch (a, [b], c)


def getFloor (x, y):
    global floor
    return floor[y][x]


def initFloor (x, y, value):
    global floor
    floor = []
    for j in range (y+1):
        row = [value] * (x+1)
        floor += [row]


#
#  toLine - returns a list containing two coordinates.
#           input:  a list of two coordinates in ascii
#           output: a list of two integer coordinates.
#

def toLine (l):
    return [[int (l[0][0]), int (l[0][1])], [int (l[1][0]), int (l[1][1])]]


#
#  vecZ - in:  a pen value n, f.
#         out:  a vector [0, 0, n/f in doom3 units]
#

def vecZ (n, f = 0):
    return [0, 0, toInches (n, f)]


#
#  vecInches - in:  a vector in pen units
#              out: returns a vector in doom3 units
#

def vecInches (vec):
    result = []
    for p in vec:
        result += [toInches (p)]
    return result


#
#  vecInches2 - in:  a vector in pen units
#               out: returns a vector in doom3 units
#

def vecInches2 (vec):
    result = []
    for p in vec:
        result += [toInches (p[0], p[1])]
    return result


cuboidno = 1          #  total number of extendable cuboids used.
cuboids = {}
roofno = 1
roofBricks = {}
polyobjno = 1         #  number of non extenable bricks used
polyobjs = {}


#
#  verify_polygon_points - runs a consistency check to ensure all points are unique.
#

def verify_polygon_points (polygon_points, name):
    for i, p in enumerate (polygon_points):
        for j, q in enumerate (polygon_points):
            if (i != j) and equVec (p, q):
                print ("polygon_points are:", polygon_points)
                print ("duplicate", p, "at indices", i, "and", j)
                error ("the polygon " + name + " must not have duplicate vertices")


class roofbrick:
    def __init__ (self, polygon_points, faces, material, transform):
        verify_polygon_points (polygon_points, "roof")
        self.polygon_points = polygon_points
        self.faces = faces
        self.material = material
        self.transform = transform


#
#  addroofbrick - adds a roof brick to the dictionary of bricks.
#                 Each roof brick has a unique number.
#                 botpos is the bottom left corner of the brick.
#                 toppos is the top left corner of the brick.
#                 foot is a list of the vectors from the top/bot pos
#                 which reference the points in the same Z plane.
#                 These are the same throughout all the Z changes of the brick.
#

def addroofbrick (polygon_points, faces, material, roomNo):
    global roofBricks, roofno

    roofBricks[roofno] = roofbrick (polygon_points, faces,
                                    lookupMaterial (roomNo, material),
                                    lookupTransform (roomNo, material))
    roofno += 1


#
#  polyobj - used to represent objects of any polygon shape which are
#            not extended.
#

class polyobj:
    def __init__ (self, polygon_points, faces, material, transform, name):
        verify_polygon_points (polygon_points, name)
        self.polygon_points = polygon_points
        self.faces = faces
        self.material = material
        self.transform = transform
        self.name = name


#
#  addpolyobj - adds a polygon brick to the dictionary of polyobjs.
#               Each brick has a unique number.
#

def addpolyobj (polygon_points, faces, material, room, name):
    global polyobjs, polyobjno

    print (polygon_points)
    polyobjs[polyobjno] = polyobj (polygon_points, faces,
                                   lookupMaterial (room, material),
                                   lookupTransform (room, material),
                                   name)
    polyobjno += 1


#
#  addcuboid - adds a cuboid brick to the dictionary of bricks.
#              Each cuboid has a unique number.
#

def addcuboid (pos, size, material, transform, fixed):
    global cuboids, cuboidno

    cuboids[cuboidno] = cuboid (pos, size, material, transform, cuboidno, fixed)
    cuboidno += 1


#
#  combined - returns True if the cuboid represented by pos, size
#             can be combined with an existing cuboid.
#

def combined (pos, size, material, transform, fixed):
    if args.debug:
        print ("examine cuboid", pos, size, end=' ')
    for k in list(cuboids.keys ()):
        b = cuboids[k]
        if (b.material != material) or (b.transform != transform):
            if b.interpenetration (pos, size):
                print ("brick at", pos, size, "intersects with", b.pos, b.size, b.cuboidno)
                error ("brick is being overwritten   (consider giving the room number for more detail)  the two cubiods have material " + b.material + " and " + material)
            # differing material cannot be merged.
            if args.debug:
                print ("differing material")
            return False
        if b.combined (pos, size, material, transform, fixed):
            if args.debug:
                print ("combined!")
            return True
    if args.debug:
        print ("no join")
    return False


#
#  alreadyExists - returns True if the cuboid already exists.
#

def alreadyExists (pos, size, material, transform):
    if args.debug:
        print ("checking", material)
    for k in list (cuboids.keys ()):
        b = cuboids[k]
        if (b.material == material) and (b.transform == transform):
            if b.subset (pos, size):
                if args.debug:
                    print ("yes found duplicate", material)
                return True
    return False


#
#
#
brickCount = 0
brickTextures = [
    "textures/hell/cbrick2",
    "textures/object/cabinettop_blk01_d",
    "textures/object/cabinettop_blue02_d",
    "textures/object/cabinettop_brnblk01_d",
    "textures/object/cabinettop_org01_d",
    "textures/object/cabinettop_white02_d"]

def chooseBrick ():
    global brickCount
    brickCount = (brickCount + 1) % len (brickTextures)
    brickCount = 0
    return brickTextures[brickCount]


#
#  newcuboid - this is the default mechanism to build a cuboid.
#              It checks whether it is possible to expand an
#              existing cuboid before creating another cuboid.
#

def newcuboid (pos, size, material, roomNo, allowExtend = True, fixed = True):
    transform = lookupTransform (roomNo, material)
    if material == "secret":
        doommat = chooseBrick ()
    else:
        doommat = lookupMaterial (roomNo, material)
    #
    #  does the cuboid already exist?  If so ignore this new cuboid request.
    #
    if not alreadyExists (pos, size, doommat, transform):
        #  are we allowed to try and extend a previous cuboid to encompass this new cuboid?
        if allowExtend:
            #  can we extend a previous cuboid to encompass this new cuboid?
            if not combined (pos, size, doommat, transform, fixed):
                # ok we must add a newcuboid
                addcuboid (pos, size, doommat, transform, fixed)
        else:
            # ok we are forced into adding a newcuboid
            addcuboid (pos, size, doommat, transform, fixed)

transformCount = None

#
#  regexpTransform - return the transformed material string if result
#                    contains a regexp.
#

def regexpTransform (roomNo, result):
    global transformCount
    i = result.find ("{")
    j = result.find ("}")
    if i != -1:
        if j == -1:
            error ("regexp is incomplete as there is no terminating } in regexp: " + result)
            os.sys.exit (1)
        before = result[:i]
        if j+1 < len (result):
            after = result[j+1:]
        else:
            after = ""
        regexp = result[i+1:j]
        if len (regexp) > 0:
            words = regexp.split(",")
            if len (words) > 0:
                fmt = words[0]
                limit = words[1].split ("-")
                transformMin = int (limit[0])
                transformMax = int (limit[1])
                if transformCount is None:
                    transformCount = transformMin
                else:
                    transformCount += 1
                if transformCount > transformMax:
                    transformCount = transformMin
                result = fmt % (random.randint (transformMin, transformMax))
                result = before + result + after
    return result


#
#  pushScope - pushes a room scope to the stack.
#

def pushScope (room):
    global scopeStack
    scopeStack = [rooms[room].defaultTextures] + scopeStack

#
#  popScope - pops a scope from the stack.
#

def popScope ():
    global scopeStack
    scopeStack = scopeStack[1:]

plinthtextureno = 0
plinthoverride = ["textures/masonary/Marble001", "textures/masonary/Marble002",
                  "textures/masonary/Marble003", "textures/masonary/Marble004",
                  "textures/masonary/Marble005", "textures/masonary/Marble006",
                  "textures/masonary/Marble007", "textures/masonary/Marble008",
                  "textures/masonary/Marble009", "textures/masonary/Marble010",
                  "textures/masonary/Marble011", "textures/masonary/Marble012",
                  "textures/masonary/Marble013",
                  "textures/masonary/Marble016", "textures/masonary/Marble020",
                  "textures/masonary/Marble021", "textures/masonary/Marble022",
                  "textures/masonary/Marble023", "textures/masonary/Marble024"]

#
#  lookupEntry - returns the entry for, name, in the stacked scope stack.
#

def lookupEntry (name):
    ### hack
    global plinthtextureno, plinthoverride
    if name == "plinth":
        plinthtextureno += 1
        if plinthtextureno == len (plinthoverride):
            plinthtextureno = 0
        return plinthoverride[plinthtextureno]
    for s in scopeStack:
        if name in s:
            return s[name]
    return None


#
#  lookupMaterial - looks up material in room and returns the result.
#                   It checks all stacked scopes.
#

def lookupMaterial (roomNo, material):
    pushScope (roomNo)
    result = lookupEntry (material)
    if result == None:
        error ("material " + material + " is not known about in room "
               + str (roomNo) + "\n")
    printf ("lookupMaterial, room %s: %s -> %s\n", roomNo, material, result)
    result = regexpTransform (roomNo, result)
    popScope ()
    return result


#
#  lookupTransform - looks up material_transform in room and returns the result.
#                    It checks all stacked scopes.
#

def lookupTransform (roomNo, material):
    pushScope (roomNo)
    result = lookupEntry (material + "_transform")
    if result == None:
        error ("transform for " + material + " is not known about in room "
               + str (roomNo) + "\n")
    popScope ()
    return result


class roomInfo:
    def __init__ (self, r, w, d):
        self.walls = orderWalls (r, w)
        self.doors = d
        self.doorLeadsTo = []
        self.pythonMonsters = []
        self.monsters = []
        self.weapons = []
        self.ammo = []
        self.lights = []
        self.worldspawn = []
        self.floorLevel = None
        self.inside = None
        self.defaultColours = {}
        self.defaultTextures = {}
        self.sounds = []
        self.labels = []
        self.plinths = []
        self.columns = []
        self.stairs = []
        self.cokeCans = []
    def addWall (self, line):
        global maxx, maxy
        line = toLine (line)
        self.walls += [line]
        maxx = max (line[0][0], maxx)
        maxx = max (line[1][0], maxx)
        maxy = max (line[0][1], maxy)
        maxy = max (line[1][1], maxy)
    def addDoor (self, line, leadsto, status):
        self.doors += [[toLine (line), leadsto, status]]
    def addAmmo (self, ammoType, ammoAmount, ammoPos):
        self.ammo += [[ammoType, ammoAmount, ammoPos]]
    def addLight (self, pos, col, on, room):
        self.lights += [[pos, light (col, on, room)]]
    def addInside (self, pos):
        self.inside = pos
    def addWeapon (self, weapon, pos):
        self.weapons += [[weapon, pos]]
    def addPythonMonster (self, monType, pos):
        self.pythonMonsters += [[monType, pos]]
    def addMonster (self, monType, pos):
        self.monsters += [[monType, pos]]
    def addPlayerSpawn (self, pos):
        self.worldspawn += [pos]
    def getNeighbours (self):
        n = []
        for d in self.doors:
            n += d[1]
        return n
    def addSound (self, s, pos):
        self.sounds += [[s, pos]]
    def addLabel (self, label, pos):
        self.labels += [[label, pos]]
    def addPlinth (self, x, y, h):
        self.plinths += [[int (x), int (y), int (h)]]
    def addColumn (self, x, y):
        self.columns += [[int (x), int (y)]]
    def addStaircase (self, staircase):
        self.stairs += [staircase]


def newRoom (n):
    global rooms
    if n in rooms:
        error ("room " + n + " has already been defined")
    rooms[n] = roomInfo (n, [], [])
    return rooms[n]


class boxInfo:
    def __init__ (self, w, d):
        self.walls = w
        self.doors = d

#
#  light - define the characteristics of the light
#

class light:
    def __init__ (self, col, on, room):
        if col == [] or col == None:
            self.col = defaultColour
        else:
            self.col = col
        self.orientation = on
        self.room = room
    def write (self, f):
        f.write ("%2f %2f %2f" % (float (self.col[0]) / 256.0, float (self.col[1]) / 256.0, float (self.col[2]) / 256.0))
    def getOn (self):
        return self.orientation
    #
    #  writeLightSource -
    #
    def writeLightSource (self, o, p):
        # print p, "getFloorLevel =", getFloorLevel (self.room)
        p = [p[0], p[1], -(p[2])]
        p = subVec (p, [minx, miny, getFloorLevel (self.room)])
        # print "after local transform, p =", p
        p = subVec (p, [minx, miny, 0])
        v = vecInches (p)
        # v = midReposition (p)
        # print "minz =", minz, "maxz =", maxz, "minx =", minx, "miny =", miny, "p =", p
        # print v
        o.write ('%f %f %f"\n' % (v[0], v[1], v[2]))
        return o


def getFloorLevel (r):
    return rooms[r].floorLevel


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
    sys.exit (1)


#
#  warning - issues a warning message and exits.
#

def warning (format, *args):
    s = str (format) % args
    sys.stderr.write (s)
    sys.exit (1)


#
#  debugf - issues prints if args.debug is set
#

def debugf (format, *args):
    if args.debug:
        print(str (format) % args, end=' ')


#
#  vprintf - verbose printf
#

def vprintf (format, *params):
    if args.verbose:
        print(str(format) % params, end=' ')
        sys.stdout.flush ()


def processDefault (d):
    global defaults
    d = d.lstrip ()
    words = d.split ()
    if (len (words) > 1) and (words[0] == 'define'):
        define = None
        expr = None
        for w in words[1:]:
            if w != "":
                if define == None:
                    define = w
                elif expr == None:
                    expr = w
        defaults[define] = expr


def readDefault (lines):
    for l in lines:
        d = l.split ('#')[0]
        d = d.rstrip ()
        processDefault (d)


def readDefaults (name):
    if name != None:
        try:
            l = open (name, 'r').readlines ()
            readDefault (l)
        except:
            print("cannot open file", name, "to read the default textures as requested")
            sys.exit (1)


#
#  initOptions - return arg which has been configured using
#                argparse.
#

def initOptions ():
    parser = argparse.ArgumentParser ()
    parser.add_argument ('-b', '--autobeams',
                         help='turn on autobeams',
                         default=False, action='store_true')
    parser.add_argument ('-d', '--debug',
                         help='generate internal debugging messages',
                         default=False, action='store_true')
    parser.add_argument ('-V', '--verbose',
                         help='generate verbose information',
                         default=False, action='store_true')
    parser.add_argument ('-y', '--style',
                         help='specify the sheet filename',
                         default=None, action='store')
    parser.add_argument ('-o', '--outputfile',
                         help='specify the output filename',
                         default=None, action='store')
    parser.add_argument ('-i', '--inputfile',
                         help='specify the input filename',
                         default=None, action='store')
    parser.add_argument ('-g', '--gametype',
                         help='specify the game type which should be single or deathmatch',
                         default='single', action='store')
    parser.add_argument ('-c', '--comments',
                         help='provide comments in the map file',
                         default=False, action='store_true')
    parser.add_argument ('-f', '--floor',
                         help='introduce steps between rooms',
                         default=False, action='store_true')
    parser.add_argument ('-m', '--map',
                         help='create a doom3 map file from the pen file',
                         default=False, action='store_true')
    parser.add_argument ('-q', '--visportals',
                         help='generate visportals at doorways',
                         default=False, action='store_true')
    parser.add_argument ('-p', '--pitch',
                         help='a pitched ceiling for four walled rooms',
                         default=False, action='store_true')
    parser.add_argument ('-s', '--statistics',
                         help='generate statistics about the map file',
                         default=False, action='store_true')
    parser.add_argument ('-t', '--txt',
                         help='create a txt file from the pen file',
                         default=False, action='store_true')
    parser.add_argument ('-E', '--ceilinglights',
                         help='enable ceiling lights',
                         default=False, action='store_true')
    parser.add_argument ('-C', '--candlelights',
                         help='enable candle lights on beams',
                         default=False, action='store_true')
    parser.add_argument ('-P', '--pillarlights',
                         help='enable lights on pillars',
                         default=False, action='store_true')
    parser.add_argument ('-F', '--floorlights',
                         help='enable lights on the floor',
                         default=False, action='store_true')
    parser.add_argument ('-O', '--optimize',
                         help='optimize cuboid generation',
                         default=False, action='store_true')
    parser.add_argument ('-v', '--version',
                         help='print the version',
                         default=False, action='store_true')
    return parser.parse_args ()


def errorLine (text):
    global currentLineNo
    full = "%s:%d:%s\n" % (args.inputfile, currentLineNo, text)
    print (full)
    sys.stderr (full)


def internalError (text):
    full = "internal error: " + text + '\n'
    sys.stderr.write (full)
    sys.exit (1)


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


def findMax (r):
    global rooms, maxx, maxy
    for w in rooms[r].walls:
        for c in w:
            maxx = max (c[0], maxx)
            maxy = max (c[1], maxy)


def floodFloor (r, p):
    if p[0] >= 0 and p[1] >= 0:
        if getFloor (p[0], p[1]) == emptyValue:
            setFloor (p[0], p[1], r)
            floodFloor (r, [p[0]-1, p[1]])
            floodFloor (r, [p[0]+1, p[1]])
            floodFloor (r, [p[0], p[1]-1])
            floodFloor (r, [p[0], p[1]+1])


def floodRoom (r, p):
    # print "floodRoom", r, p,
    if args.debug:
        if getFloor (p[0], p[1]) == emptyValue:
            print("will start")
        else:
            print("will not start", getFloor (p[0], p[1]))
    floodFloor (int (r), p)


def findDoors (r, p):
    for d in rooms[r].doors:
        if d[0][0] == d[1][0]:
            # vertical door
            if getFloor (d[0][0]+1, d[0][1]) != int (r):
                rooms[r].doorLeadsTo += [getFloor (d[0][0]+1, d[0][1])]
            else:
                rooms[r].doorLeadsTo += [getFloor (d[0][0]-1, d[0][1])]
        else:
            # horizontal
            if getFloor (d[0][0], d[0][1]+1) != int (r):
                rooms[r].doorLeadsTo += [getFloor (d[0][0], d[0][1]+1)]
            else:
                rooms[r].doorLeadsTo += [getFloor (d[0][0], d[0][1]-1)]


def doGetToken ():
    global words
    if len (words) > 1:
        return words[0], words[1:]
    elif len (words) == 1:
        return words[0], ['<eof>']


def expectEoln ():
    global currentLineNo, words
    if words[0] == '<eoln>':
        currentLineNo += 1
        words = words[1:]


#
#  get - returns the next token and the remainder of the words.
#

def get ():
    global currentLineNo, words
    n, words = doGetToken ()
    while n == '<eoln>':
        expectEoln ()
        n, words = doGetToken ()
    return n


#
#  peek - returns the first token without removing it from input.
#         It will advance the linenumber if <eoln> is seen.
#

def peek ():
    global currentLineNo, words
    n = words[0]
    while n == '<eoln>':
        expectEoln ()
        return peek ()
    return n


#
#  expect - expect a token, t.
#

def expect (t):
    # print "expect", t,
    g = get ()
    """
    print "seen", g
    print "seen", g,
    if g == t:
        print "the same"
    else:
        print "not the same"
    """
    if g != t:
        errorLine ('expecting ' + t + ' and seen ' + g)


#
#  expecting - return True if the next token is one of, l.
#

def expecting (l):
    t = peek ()
    """
    print "expecting one of", l, "and we have", t,
    if t in l:
        print "match"
    else:
        print "no match"
    """
    return t in l


#
#  lexicalPen - return a list of tokens to be read by the parser.
#               A special token <eoln> is added at the end of each line.
#               <eof> is added at the end.
#

def lexicalPen (i):
    words = []
    for l in i.readlines ():
        w = l.split ()
        w += ['<eoln>']
        for j in w:
            if j != "":
                i = j.rstrip ()
                words += [i]
    words += ['<eof>']
    return words


#
#  wallCoords := Integer Integer Integer Integer =:
#

def wallCoords ():
    global curRoom
    if integer ():
        x0 = curInteger
        if integer ():
            y0 = curInteger
            if integer ():
                x1 = curInteger
                if integer ():
                    y1 = curInteger
                    curRoom.addWall ([[x0, y0], [x1, y1]])
                    return True
                else:
                    errorLine ('expecting fourth integer for a wall')
            else:
                errorLine ('expecting third integer for a wall')
        else:
            errorLine ('expecting second integer for a wall')
    return False


#
# WallDesc := 'WALL' WallCoords { WallCoords } =:
#

def wallDesc ():
    expect ('WALL')
    if wallCoords ():
        while wallCoords ():
            pass


#
# PlinthDesc := 'PLINTH' int int int =:
#

def plinthDesc ():
    expect ('PLINTH')
    global curRoom
    if integer ():
        x = curInteger
        if integer ():
            y = curInteger
            if integer ():
                h = curInteger
                curRoom.addPlinth (x, y, h)
            else:
                errorLine ('expecting third integer, the height, for a plinth')
        else:
            errorLine ('expecting second integer, the Y axis, for a plinth')
    else:
        errorLine ('expecting first integer, the X axis, for a plinth')


#
#  status := "STATUS" ( [ 'OPEN' | 'CLOSED' | 'SECRET' ] ) =:
#

def status ():
    global curStatus
    expect ('STATUS')
    if expecting (['OPEN', 'CLOSED', 'SECRET']):
        if expecting (['OPEN']):
            curStatus = status_open
            expect ('OPEN')
        elif expecting (['CLOSED']):
            curStatus = status_closed
            curStatus = status_open    # --fixme-- closed doors would be nice!
            expect ('CLOSED')
        elif expecting (['SECRET']):
            curStatus = status_secret
            expect ('SECRET')
        return True
    return False


#
#  integer - if the next token is an integer then
#               consume it and save it into curInteger
#               return True
#            else:
#               return False
#

def integer ():
    global curInteger
    i = peek ()
    if i.isdigit () or (i[0] == '-'):
        curInteger = get ()
        # print "found integer", curInteger, "next token is", peek ()
        return True
    # print "not an integer"
    return False


#
#  doorCoords := integer integer integer integer status "LEADS" "TO" integer =:
#

def doorCoords ():
    global curRoom
    if integer ():
        x0 = curInteger
        if integer ():
            y0 = curInteger
            if integer ():
                x1 = curInteger
                if integer ():
                    y1 = curInteger
                    if status ():
                        expect ("LEADS")
                        expect ("TO")
                        if integer ():
                            leadsTo = curInteger
                            curRoom.addDoor ([[x0, y0], [x1, y1]], leadsTo, curStatus)
                            return True
                else:
                    errorLine ('expecting fourth integer for a wall')
            else:
                errorLine ('expecting third integer for a wall')
        else:
            errorLine ('expecting second integer for a wall')
    return False


#
#  doorDesc := "DOOR" doorCoords { doorCoords } =:
#

def doorDesc ():
    expect ('DOOR')
    if doorCoords ():
        while doorCoords ():
            pass
        return True
    return False


#
#  posDesc := integer integer =:
#

def posDesc ():
    global curPos
    if integer ():
        x = curInteger
        if integer ():
            curPos = [x, curInteger]
            return True
        else:
            errorLine ('expecting second integer in the position pair')
    return False


#
#  ammoDesc := "AMMO" integer "AMOUNT" integer "AT" posDesc =:
#

def ammoDesc ():
    expect ('AMMO')
    ammoType = get ()
    expect ('AMOUNT')
    if integer ():
        ammoAmount = curInteger
        expect ('AT')
        if posDesc ():
            ammoPos = curPos
            curRoom.addAmmo (ammoType, ammoAmount, ammoPos)
        else:
            errorLine ('expecting a position for the ammo')
    else:
        errorLine ('expecting an amount of ammo')


#
#  colDesc - expects a colour r g b (three integers).
#            It assigns these to curCol.
#

def colDesc ():
    global curCol
    curCol = []
    if integer ():
        curCol += [curInteger]
        if integer ():
            curCol += [curInteger]
            if integer ():
                curCol += [curInteger]
            else:
                errorLine ('expecting green colour component')
        else:
            errorLine ('expecting blue colour component')
    else:
        errorLine ('expecting red colour component')


#
#  onDesc - returns True if ON string is seen.
#

def onDesc ():
    global curOn
    if expecting (['ON']):
        expect ('ON')
        curOn = get ()
        return True
    return False


#
#  scopeColour - return the default colour for a room or global default colour
#                if col is not set.
#

def scopeColour (col):
    if col == []:
        if curOn in curRoom.defaultColours:
            return curRoom.defaultColours[curOn]
        return defaultColour
    return col


#
#  scopeColourRoom - return the default colour for a room or global default colour
#                    if one has not been defined.
#

def scopeColourRoom (r, on):
    if on in rooms[r].defaultColours:
        return rooms[r].defaultColours[on]
    return defaultColour


#
#  lightDesc := 'LIGHT' 'AT' posDesc [ 'COLOUR' int int int ] [ 'ON' string ] =:
#

def lightDesc ():
    global curCol, curOn
    expect ('LIGHT')
    expect ('AT')
    if posDesc ():
        curCol = []
        curOn = defaultOn
        if expecting (['COLOUR']):
            expect ('COLOUR')
            colDesc ()
        if onDesc ():
            pass
        curRoom.addLight (curPos, scopeColour (curCol), curOn, curRoomNo)
        return True
    else:
        errorLine ('expecting a position for a light')
        return False


#
#  insideDesc := 'INSIDE' 'AT' posDesc =:
#

def insideDesc ():
    expect ('INSIDE')
    expect ('AT')
    if posDesc ():
        curRoom.addInside (curPos)
        return True
    else:
        errorLine ('expecting a position for an inside declaration')
        return False


#
#  weaponDesc := 'WEAPON' 'AT' posDesc =:
#

def weaponDesc ():
    expect ('WEAPON')
    if integer ():
        weapon = curInteger
        expect ('AT')
        if posDesc ():
            curRoom.addWeapon (weapon, curPos)
            return True
        else:
            errorLine ('expecting a position for a weapon')
    else:
        errorLine ('expecting a weapon number')
    return False


#
#  labelDesc := 'LABEL' 'AT' posDesc string =:
#

def labelDesc ():
    expect ('LABEL')
    expect ('AT')
    if posDesc ():
        label = get ()
        curRoom.addLabel (label, curPos)
        return True
    else:
        errorLine ('expecting a position for a label')
    return False


#
#  monsterDesc := 'MONSTER' type 'AT' posDesc =:
#

def monsterDesc ():
    expect ('MONSTER')
    monType = get ()
    expect ('AT')
    if posDesc ():
        if (len (monType) > len ("python_")) and ("python_" == monType[:len ("python_")]):
            curRoom.addPythonMonster (monType, curPos)
        else:
            curRoom.addMonster (monType, curPos)
        return True
    else:
        errorLine ('expecting a position for a monster')
    return False


#
#  spawnDesc := "SPAWN" "PLAYER" "AT" posDesc =:
#

def spawnDesc ():
    expect ('SPAWN')
    expect ('PLAYER')
    expect ('AT')
    if posDesc ():
        curRoom.addPlayerSpawn (curPos)
        return True
    else:
        errorLine ('expecting a position for a player spawn')
    return False


#
#  defaultConfig := "COLOUR" defaultColourConfig |
#                   "TEXTURE" defaultTextureConfig =:
#

def defaultConfig ():
    if expecting (['COLOUR']):
        defaultColourConfig ()
    elif expecting (['TEXTURE']):
        defaultTextureConfig ()
    else:
        errorLine ('expecting COLOUR or TEXTURE after DEFAULT')

#
#  defaultTextureConfig := ( "CEILING" | "FLOOR" | "WALL" | "PLINTH" ) string =:
#

def defaultTextureConfig ():
    expect ('TEXTURE')
    if expecting (['CEILING']):
        expect ('CEILING')
        curRoom.defaultTextures['ceiling'] = get ()
    elif expecting (['FLOOR']):
        expect ('FLOOR')
        curRoom.defaultTextures['floor'] = get ()
    elif expecting (['WALL']):
        expect ('WALL')
        curRoom.defaultTextures['wall'] = get ()
    elif expecting (['PLINTH']):
        expect ('PLINTH')
        curRoom.defaultTextures['plinth'] = get ()
    elif expecting (['BEAM']):
        expect ('BEAM')
        curRoom.defaultTextures['beam'] = get ()
    else:
        errorLine ("expecting FLOOR, WALL, CEILING and PLINTH after DEFAULT TEXTURE")

#
#  defaultColourConfig := "COLOUR" ( "CEILING" | "MID" | "FLOOR" ) int int int =:
#

def defaultColourConfig ():
    expect ('COLOUR')
    if expecting (['FLOOR']):
        expect ('FLOOR')
        colDesc ()
        curRoom.defaultColours['FLOOR'] = curCol
    elif expecting (['MID']):
        expect ('MID')
        colDesc ()
        curRoom.defaultColours['MID'] = curCol
    elif expecting (['CEILING']):
        expect ('CEILING')
        colDesc ()
        curRoom.defaultColours['CEIL'] = curCol
    else:
        errorLine ("expecting FLOOR, MID or CEILING after DEFAULT COLOUR")

#
#  defaultDesc := "DEFAULT" defaultConfig =:
#

def defaultDesc ():
    expect ("DEFAULT")
    defaultConfig ()


class sound:
    def __init__ (self, filename):
        self.filename = filename
        self.volume = 0.0
        self.looping = 1
        self.wait = 0.0
        self.mindist = 3.0
        self.maxdist = 25.0
    def setVolume (self, volume):
        self.volume = volume
    def setLooping (self):
        self.looping = True
    def setWait (self, wait):
        self.wait = wait


#
#  soundDesc := "SOUND" "AT" { volumeDesc | loopingDesc | waitDesc } =:
#

def soundDesc ():
    expect ("SOUND")
    expect ("AT")
    if posDesc ():
        soundPos = curPos
        filename = get ()
        s = sound (filename)
        while expecting (['VOLUME', 'LOOPING', 'WAIT']):
            if expecting (['VOLUME']):
                expect ('VOLUME')
                if integer ():
                    s.setVolume (curInteger)
                else:
                    errorLine ('expecting an integer after the VOLUME keyword')
            elif expecting (['LOOPING']):
                expect ('LOOPING')
                s.setLooping ()
            elif expecting (['WAIT']):
                expect ('WAIT')
                if integer ():
                    s.setWait (curInteger)
                else:
                    errorLine ('expecting an integer after the WAIT keyword')
        curRoom.addSound (s, soundPos)



#
#  roomDesc := "ROOM" integer { doorDesc | wallDesc | treasureDesc | ammoDesc | lightDesc | insideDesc | weaponDesc | monsterDesc | spawnDesc | defaultDesc | soundDesc } =:
#

def roomDesc ():
    global curRoom, curInteger, curRoomNo
    if expecting (['ROOM']):
        expect ("ROOM")
        if integer ():
            curRoomNo = curInteger
            curRoom = newRoom (curRoomNo)
            if args.debug:
                print("roomDesc", curRoomNo)
            while expecting (['DOOR', 'WALL', 'TREASURE', 'AMMO', 'WEAPON', 'LIGHT', 'INSIDE', 'MONSTER', 'SPAWN', 'DEFAULT', 'SOUND', 'LABEL', 'PLINTH', 'STAIRCASE', 'COLUMN']):
                if expecting (['DOOR']):
                    doorDesc ()
                elif expecting (['WALL']):
                    wallDesc ()
                elif expecting (['TREASURE']):
                    treasureDesc ()
                elif expecting (['AMMO']):
                    ammoDesc ()
                elif expecting (['WEAPON']):
                    weaponDesc ()
                elif expecting (['LABEL']):
                    labelDesc ()
                elif expecting (['LIGHT']):
                    lightDesc ()
                elif expecting (['INSIDE']):
                    insideDesc ()
                elif expecting (['MONSTER']):
                    monsterDesc ()
                elif expecting (['SPAWN']):
                    spawnDesc ()
                elif expecting (['DEFAULT']):
                    defaultDesc ()
                elif expecting (['SOUND']):
                    soundDesc ()
                elif expecting (['PLINTH']):
                    plinthDesc ()
                elif expecting (['COLUMN']):
                    columnDesc ()
                elif expecting (['STAIRCASE']):
                    staircaseDesc ()
            expect ('END')
            return True
        else:
            errorLine ('expecting an integer after ROOM')
    return False


def columnDesc ():
    global curRoom
    if expecting (['COLUMN']):
        expect ("COLUMN")
        if integer ():
            x = curInteger
            if integer ():
                y = curInteger
                curRoom.addColumn (x, y)
                return True
            else:
                errorLine ('expecting an integer for the y position for the column')
        else:
            errorLine ('expecting an integer for the x position for the column')
    return False


#
#
#

def orientDesc ():
    if expecting (['NORTH']):
        expect ("NORTH")
        return 0
    if expecting (['EAST']):
        expect ("EAST")
        return 1
    if expecting (['SOUTH']):
        expect ("SOUTH")
        return 2
    if expecting (['WEST']):
        expect ("WEST")
        return 3
    errorLine ('expecting NORTH, EAST, SOUTH, WEST')



#
#  staircaseDesc := 'STAIRCASE' x y
#                    ( 'NORTH' | 'EAST' | 'SOUTH' | 'WEST' )
#                    ( 'CLOCKWISE' | 'ANTICLOCK' )
#                    ( 'UP' | 'DOWN' ) 'TO' dest =:
#

def staircaseDesc ():
    if expecting (['STAIRCASE']):
        expect ("STAIRCASE")
        if integer ():
            x = curInteger
            if integer ():
                y = curInteger
                orient = orientDesc ()
                if expecting (['CLOCKWISE', 'ANTICLOCK']):
                    if expecting (['CLOCKWISE']):
                        expect ('CLOCKWISE')
                        clockwise = True
                    else:
                        expect ('ANTICLOCK')
                        clockwise = False
                    if expecting (['UP', 'DOWN']):
                        if expecting (['UP']):
                            expect ('UP')
                            up = True
                        else:
                            expect ('DOWN')
                            up = False
                        if expecting (['TO']):
                            expect ('TO')
                            if integer ():
                                dest = curInteger
                                curRoom.addStaircase (staircase (x, y,
                                                                 orient,
                                                                 clockwise, up,
                                                                 dest))
                                return True
                            else:
                                errorLine ('expecting integer dest')
                    else:
                        errorLine ('expecting UP or DOWN')
                else:
                    errorLine ('expecting CLOCKWISE or ANTICLOCK')
            else:
                errorLine ('expecting integer y coordinate')
        else:
            errorLine ('expecting integer x coordinate')
    return False


#
#  parsePen := roomDesc { roomDesc } randomTreasure "END." =:
#

def parsePen ():
    if roomDesc ():
        while roomDesc ():
            pass
        # if randomTreasure ():
        #    pass
        expect ("END.")
        return True
    return False


#
#  getPos - return the coordinate pair in wall or door, p.
#

def getPos (p):
    return int (p[0]), int (p[1])


#
#  toIntList - pre-condition:  a list of integers or strings of integers.
#              post-condition:  returns a list of integers.
#

def toIntList (l):
    result = []
    for c in l:
        result += [int (c)]
    return result


#
#  plotLine - draws a line described by, l, using character, value.
#

def plotLine (l, value):
    x0, y0 = getPos (l[0])
    x1, y1 = getPos (l[1])
    if x0 == x1:
        for j in range (min (y0, y1), max (y0, y1)+1):
            setFloor (x0, j, value)
    else:
        for i in range (min (x0, x1), max (x0, x1)+1):
            setFloor (i, y0, value)


#
#  generateTxtRoom - generate a text representation of the pen map.
#

def generateTxtRoom (r):
    for w in rooms[r].walls:
        plotLine (w, '#')
    for d in rooms[r].doors:
        if d[2] == status_open:
            plotLine (d[0], '.')
        elif d[2] == status_closed:
            if d[0][0][0] == d[0][1][0]:
                plotLine (d[0], '|')
            else:
                plotLine (d[0], '-')
        elif d[2] == status_secret:
            plotLine (d[0], '=')


#
#  generateTxt - generate an ascii .txt file containing the map.
#

def generateTxt (o):
    initFloor (maxx, maxy, ' ')
    for r in list(rooms.keys ()):
        generateTxtRoom (r)
    floor.reverse ()
    for r in floor:
        for c in r[1:]:
            o.write (c)
        o.write ('\n')
    return o


#
#  generateVersion - display the version number.
#

def generateVersion (o):
    o.write ("Version 2\n")
    return o


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
#  isLower - return True if line, a, is lower than, b.
#

def isLower (a, b):
    return min (a[0][1], a[1][1]) < min (b[0][1], b[1][1])


#
#  isSameLowerHeight - return True if line, a, is the same
#                      height as, b.  It only considers the
#                      lower coordinate.
#

def isSameLowerHeight (a, b):
    return min (a[0][1], a[1][1]) == min (b[0][1], b[1][1])


#
#  isLeft - return True if line, a, is left of, b.
#

def isLeft (a, b):
    return min (a[0][0], a[1][0]) < min (b[0][0], b[1][0])


#
#  getLowest - return the lowest coordinate of the line.
#

def getLowest (c):
    if c[0][1] < c[1][1]:
        return c[0]
    return c[1]


#
#  getHighest - return the highest coordinate of the line.
#

def getHighest (c):
    if c[0][1] > c[1][1]:
        return c[0]
    return c[1]


#
#  getLeft - return the left coordinate of the line.
#

def getLeft (c):
    if c[0][0] < c[1][0]:
        return c[0]
    return c[1]


#
#  getRight - return the right coordinate of the line.
#

def getRight (c):
    if c[0][0] > c[1][0]:
        return c[0]
    return c[1]


#
#  findLowestLeftVertical - return the indice of the lowest
#                           left vertical wall in, w.
#                           The lower coordinate will always
#                           take precedence and after that
#                           leftwards.
#

def findLowestLeftVertical (w):
    best = None
    j = None
    for i, c in enumerate (w):
        if isVertical (c):
            if (best == None) or isLower (c, best):
                best = c
                j = i
            elif isSameLowerHeight (c, best) and isLeft (c, best):
                best = c
                j = i
    return j


#
#  findJoining - find the
#

def findJoining (r, w, e, p):
    for i, l in enumerate (w):
        if isVertical (l) and (getLowest (l) == e):
            return i
        if isVertical (l) and (getHighest (l) == e):
            return i
        if isHorizontal (l) and (getLeft (l) == e):
            return i
        if isHorizontal (l) and (getRight (l) == e):
            return i
    if args.debug:
        print("w =", w)
        print("e =", e)
        print("p =", p)
    internalError ('walls do not form a bounded room in room ' + str (r))


def include (p, i):
    if p == None or p == []:
        return [i]
    for e in p:
        if i == e:
            return p
    return p + [i]


#
#  orderWalls - return a clockwise ordered list of walls
#

def orderWalls (r, w):
    if w == [] or w == None:
        return w
    w = w[:]  # make a new copy of w
    if args.debug:
        print("orderWalls, entered")
        for i in w:
            print(i)
    n = []
    i = findLowestLeftVertical (w)
    if args.debug:
        print("findLowestLeftVertical =", i)
    n += [sortWall (w[i])]
    e = getHighest (w[i])
    if args.debug:
        print("w[i] =", w[i], "e =", e)
    p = [getLowest (w[i])]
    if args.debug:
        print("i =", i)
        print("w =", w)
        print("n =", n)
        print("i =", i)
        print("p =", p)
        print("loop")
    del w[i]
    while w != []:
        i = findJoining (r, w, e, p)
        n += [sortWall (w[i])]
        if args.debug:
            print("i =", i)
            print("n =", n)
            print("2nd p =", p)
            print("w =", w)
        p = include (p, w[i][0])
        p = include (p, w[i][1])
        if e == w[i][0]:
            e = w[i][1]
        else:
            e = w[i][0]
        if args.debug:
            print("3rd p =", p, "e =", e)
        del w[i]
    if args.debug:
        print("orderWalls, exiting with", n)
    if not isVertical (n[0]):
        internalError ('expecting first wall to be vertical')
    return n


def createBoxes (r, w, d):
    if args.debug:
        print("createBoxes", r, w, d)
    if len (w) == 4:
        # must be a single box
        return [boxInfo (w, d)]
    # more than 4 walls, split into two or more boxes
    print("needs splitting", w, d)
    sys.exit (1)
    return [boxInfo (w, d)]
    sys.stderr ('--fixme-- this needs completing\n')


#
#  onWall - return True if door is on wall.
#

def onWall (wall, door):
    if isVertical (wall) and isVertical (door):
        return wall[0][0] == door[0][0]
    if isHorizontal (wall) and isHorizontal (door):
        return wall[0][1] == door[0][1]
    return False


#
#  sortWall - order a wall coordinate left, bottom to right, top
#

def sortWall (w):
    if args.debug:
        print("sortwall", w)
    if isVertical (w):
        if w[0][1] > w[1][1]:
            return [w[1], w[0]]
        return w
    if isHorizontal (w):
        if w[0][0] > w[1][0]:
            return [w[1], w[0]]
        return w
    print("wall problem", w)
    internalError ('wall must be horizontal or vertical')


#
#  sortDoors - return the list of doors, ordered left
#              to right and bottom to top
#

def sortDoors (doors, door):
    if doors == []:
        return [door]
    if isVertical (door[0]):
        for i, d in enumerate (doors):
            if isLower (door[0], d[0]):
                return doors[:i] + [door] + doors[i:]
        return doors + [door]
    if isHorizontal (door[0]):
        for i, d in enumerate (doors):
            if isLeft (door[0], d[0]):
                return doors[:i] + [door] + doors[i:]
        return doors + [door]


#
#  getDoors - returns the doors which are on wall, w.
#             The doors are ordered.
#

def getDoors (w, d):
    doors = []
    for x in d:
        if onWall (w, x[0]):
            doors = sortDoors (doors, x)
    return doors


#
#  entityWall - create an entity representing a wall from
#               start to end along direction, d.
#

def entityWall (start, end, d):
    if args.debug:
        print("entityWall", start, end, d)
    if isHorizontal ([start, end]) or isVertical ([start, end]):
        return [[start, end, "wall", direction[d]]]
    print(start, end, "direction d=", d)
    internalError ('wall must be either vertical or horizontal')


def entityDoor (start, end, d, door):
    return [[start, end, doorStatus[door[2]], direction[d]]]


def orderCoords (line, direction):
    if isVertical (line):
        if direction == 0:
            # left
            if line[0][1] > line[1][1]:
                return line[1], line[0]
            return line[0], line[1]
        else:
            # right
            if line[0][1] > line[1][1]:
                return line[1], line[0]
            return line[0], line[1]
    else:
        if direction == 1:
            # top
            if line[0][0] > line[1][0]:
                return line[1], line[0]
            return line[0], line[1]
        else:
            # bottom
            if line[0][0] > line[1][0]:
                return line[1], line[0]
            return line[0], line[1]



#
#  lastWallPos - p is the door coordinate.  i is the direction
#                [left, top, right, bottom].  Return the left or
#                lower coordinate where the end of the wall
#                finished.
#

def lastWallPos (p, i):
    if (i == 0) or (i == 2):
        return [p[0], p[1]-1]
    return [p[0]-1, p[1]]


#
#  nextWallPos - p is the door coordinate.  i is the direction
#                [left, top, right, bottom].  Return the left or
#                upper coordinate where the start of the wall
#                continues.
#

def nextWallPos (p, i):
    if (i == 0) or (i == 2):
        return [p[0], p[1]+1]
    return [p[0]+1, p[1]]


#
#  wallToEntity - returns a list of entities representing
#                 the wall, w, i.  It will take into
#                 consideration the doors, d.
#

def wallToEntity (w, i, d):
    if (i == 0) or (i == 2):
        if not isVertical (w):
            print(w, i)
            internalError ('wallToEntity: expecting wall to be vertical')
    elif (i == 1) or (i == 3):
        if not isHorizontal (w):
            print(w, i)
            internalError ('wallToEntity: expecting wall to be horizontal')

    e = []
    dl = getDoors (w, d)
    if dl == []:
        # no doors just a wall
        return entityWall (w[0], w[1], i)
    p = w[0]
    for di in dl:
        f, s = orderCoords (di[0], i)
        e += entityWall (p, lastWallPos (f, i), i)
        e += entityDoor (f, s, i, di)
        p = nextWallPos (s, i)
    e += entityWall (p, w[1], i)
    return e


#
#  convertBoxesToEntities - converts a box into an entity.
#                           A box only has four sides and
#                           the list is ordered
#                           [left, top, right, bottom]
#

def convertBoxesToEntities (b):
    e = []
    for x in b:
        for i, w in enumerate (x.walls):
            e += wallToEntity (w, i, x.doors)
    return e


#
#  movesRight - returns True if wall, w, moves point, p, right.
#

def movesRight (w, p):
    if equVec (w[0], p):
        return w[1][0] > p[0]
    else:
        return w[0][0] > p[0]


#
#  movesLeft - returns True if wall, w, moves point, p, left.
#

def movesLeft (w, p):
    if equVec (w[0], p):
        return w[1][0] < p[0]
    else:
        return w[0][0] < p[0]


#
#  movesUp - returns True if wall, w, moves point, p, up.
#

def movesUp (w, p):
    if equVec (w[0], p):
        return w[1][1] > p[1]
    else:
        return w[0][1] > p[1]


#
#  movesDown - returns True if wall, w, moves point, p, down.
#

def movesDown (w, p):
    if equVec (w[0], p):
        return w[1][1] < p[1]
    else:
        return w[0][1] < p[1]


#
#  checkOnWall - performs a consistency check to see that
#                p is at one end of w.
#

def checkOnWall (r, p, w):
    if not (equVec (p, w[0]) or equVec (p, w[1])):
        print("room", r, "has a problem with a wall, ", w, "p is not on either end", p)
        sys.exit (1)


def createWallDoorList (r, walls, doors):
    if args.debug:
        print("createWallDoorList")
        print("==================")
        print("room", r, "has walls")
        for i in walls:
            print(i)
        print("room", r, "has doors")
        for i in doors:
            print(i)
    e = []
    d = 0   # direction is left
    p = walls[0][0]
    if args.debug:
        print("lowest left, p =", p)
    for i, w in enumerate (walls):
        if args.debug:
            print("direction", d, "position", p, "looking at", w)
        checkOnWall (r, p, w)
        if (d == 0) or (d == 2):
            # on left or right vertical wall
            if movesRight (w, p):
                d = 1  # from left to top wall
                if args.debug:
                    print("moves to top because of wall", w)
            elif movesLeft (w, p):
                d = 3  # from left to bottom wall
                if args.debug:
                    print("moves to bottom because of wall", w)
        else:
            # must be on either top or bottom wall
            if movesUp (w, p):
                d = 0  # from top/bottom to left vertical wall
                if args.debug:
                    print("moves to left because of wall", w)
            elif movesDown (w, p):
                d = 2  # from top/bottom to right vertical wall
                if args.debug:
                    print("moves to right because of wall", w)
        if (d == 0) or (d == 2):
            if not isVertical (w):
                print(w, d)
                internalError ('createWallDoorList: expecting wall to be vertical')
        elif (d == 1) or (d == 3):
            if not isHorizontal (w):
                print(w, d)
                internalError ('createWallDoorList: expecting wall to be horizontal')

        e += wallToEntity (w, d, doors)
        if equVec (p, w[0]):
            p = w[1]
        else:
            p = w[0]
        if args.debug:
            print("entity list", e)
    if args.debug:
        print("entity list is", e)
    return e


def roomToEntities (r):
    w = orderWalls (r, rooms[r].walls)
    if args.debug:
        print("ordered walls =", w)
    return createWallDoorList (r, w, rooms[r].doors)


#
#  invertAxis - flip the sign of the value, a.
#               This function is used to aid debugging.
#

def invertAxis (a):
    return -a


#
#  toInches - f/i is effectively base 48 (inches).
#             in: f, i   f is a whole number, i is the fractional component of the doom3 value in inches.
#             out:  return f*inchesPerUnit + i
#
#             the value is limit checked.
#

def toInches (f, i = 0):
    d3 = f*inchesPerUnit+i
    if d3 >= maxd3Units:
        error ("this map is too large, it must not exceed %d doom3 units square or %d pen units square\n", d3, maxd3Units / inchesPerUnit)
    d3 = invertAxis (d3)
    return d3


#
#  writeComment - writes out a comment if it exists.
#

def writeComment (o, comment):
    if comment != "":
        o.write ('             ')
        o.write ('// ' + comment + '\n')
    return o


#
#  yPlane -
#

def yPlane (o, d, x0, text, transform, comment):
    o = writeComment (o, comment)
    o.write ('             ')
    o.write ('( 0 ' + str (d) + ' 0 ' + str (x0) + ' ) ')
    o.write (transform + ' "' + text + '" 0 0 0\n')
    return o

#
#  xPlane -
#

def xPlane (o, d, y0, text, transform, comment):
    o = writeComment (o, comment)
    o.write ('             ')
    o.write ('( ' + str (d) + ' 0 0 ' + str (y0) + ' ) ')
    o.write (transform + ' "' + text + '" 0 0 0\n')
    return o


#
#  zPlane - d is the direction of the zPlane, z0 is the offset from the origin.
#

def zPlane (o, d, z0, text, transform, comment):
    assert (z0 != 0)
    o = writeComment (o, comment)
    o.write ('             ')
    o.write ('( 0 0 ' + str (d) + ' ' + str (-z0) + ' ) ')
    o.write (transform + ' "' + text + '" 0 0 0\n')
    return o

#
#  simplify_unit - convert a floating point number to an integer if they are the same value.
#

def simplify_unit (unit):
    if isEpsilon (unit, 0.000001):
        return 0
    if abs (unit) == unit:
        unit = abs (unit)
    if int (unit) == unit:
        unit = int (unit)
    return unit

#
#  simplify_vec - convert a vector of floating point values into a vector of integers providing
#                 the values are the same.
#

def simplify_vec (vec):
    v = []
    for e in vec:
        v += [simplify_unit (e)]
    return v


#
#  plane - emit a plane defined by vector, vec, having a, distance, away
#          from the origin into the map.  The plane has material and a transform.
#          The caller may give a comment which appears in the map file.
#

def plane (o, vec, distance, material, transform, comment):
    vec = simplify_vec (vec)
    distance = simplify_unit (distance)
    o = writeComment (o, comment)
    o.write ('             ')
    o.write ('( ' + str (vec[0]) + ' ' + str (vec[1])
             + ' ' + str (vec[2]) + ' ' + str (distance) + ' ) ')
    o.write (transform + ' "' + material + '" 0 0 0\n')
    return o


def mag (v):
    d = 0
    for i in v:
        d += i*i
    return d


#
#  reorderVertices
#
#  reorder the coordinates (vertices) which describe a cubiod.
#  v0 and v1 are the input vertices.
#  returns two new vertices w0 and w1.
#  w0 is the bottom left hand corner
#  w1 is the top right hand corner.
#

def reorderVertices (v0, v1):
    assert (len (v0) == len (v1))
    w0 = []
    w1 = []
    for i, j in zip (v0, v1):
        w0 += [min (i, j)]
        w1 += [max (i, j)]
    return w0, w1



#
#  brick - generate a solid brick using two vertices (corners)
#          v0 and v1 must be opposite corners of the cuboid.
#          v0 = [x, y, z]
#          v1 = [x, y, z]
#

def brick (o, v0, v1, material, transform):
    v0 = translatePos (v0)
    v1 = translatePos (v1)
    v0, v1 = reorderVertices (v0, v1)
    size = subVec (v1, v0)
    points, faces = generate_cube_points (v0, v1)
    o = roof (o, points, faces, material, transform)
    return o


def sqr (x):
    return x * x


#
#  gcd - pre-condition:  given two numbers: a, b
#        post-condition: return the greatest common denominator from: a, b.
#

def gcd (a, b):
    if a < 0:
        a = -a
    if b < 0:
        b = -b
    while b != 0:
        t = b
        b = a % b
        a = t
    return a

#
#  gcd3 - pre-condition:  given three numbers: a, b, c
#         post-condition: return the greatest common denominator from: a, b, c.
#

def gcd3 (a, b, c):
   return gcd (a, gcd (b, c))


#
#  gcd4 - pre-condition:  given three numbers: a, b, c, d
#         post-condition: return the greatest common denominator from: a, b, c, d.
#

def gcd4 (a, b, c, d):
   return gcd (a, gcd (b, gcd (c, d)))


#
#  simplify - pre-condition:  given a vector of three numbers: a, b, c, d
#             post-condition: return the smallest equivalent values using
#                             the greatest common denominator as the divisor.
#

def simplify (a, b, c, d):
    e = gcd4 (a, b, c, d)
    a /= e
    b /= e
    c /= e
    d /= e
    return a, b, c, d

#
#  distance - return the closest distance any point on the plane lies
#             from the origin.
#

def distance (p, a, b, c):
    d = - (p[0] * a + b * p[1] + c * p[2])
    return d


#
#  plane_formula - pre-condition:  v0 and v1 are vectors defining the plane.
#                  post-condition: return [a, b, c, d] where
#                                  ax + by + cz + d = 0
#                                  which defines the plane.
#

def plane_formula (p, v0, v1):
    # print "point on plane =", p, "v0 =", v0, "v1 =", v1
    a, b, c = crossProduct (v0, v1)
    a, b, c = normaliseVec ([a, b, c])
    # print "cross product (", v0, " x ", v1, ") =", [a, b, c],
    d = distance (p, a, b, c)
    # print "distance =", d
    return a, b, c, d


#
#  plane_distance - return the distance of the plane from the origin
#

def plane_distance (a, b, c, d):
    abc2 = sqr (a) + sqr (b) + sqr (c)
    #
    #  find the closest point to the origin
    #
    x = a * d / abc2
    y = b * d / abc2
    z = c * d / abc2
    #
    #  and compute the distance of (x, y, z) from the origin.
    #
    return math.sqrt (sqr (x) + sqr (y) + sqr (z))

#
#  calc_face - return two objects, a plane and distance of a face.
#

def calc_face (p0, p1, p2):
    # print "***********", p0, p1, p2
    v0 = subVec (p1, p0)
    v1 = subVec (p2, p0)
    #
    #  convert to doom3 units
    #
    p0 = decimalVec (vecInches (p0))
    v0 = decimalVec (vecInches (v0))
    v1 = decimalVec (vecInches (v1))
    a, b, c, d = plane_formula (p0, v1, v0)
    return [a, b, c], d


def isEpsilon (r, e = 0.0001):
    return abs (r) < e


def isNearZero (r):
    return isEpsilon (r, 0.1)


def verify_point_on_plane (vec, distance, p):
    p = decimalVec (vecInches (p))
    A = vec[0] * p[0]
    B = vec[1] * p[1]
    C = vec[2] * p[2]
    D = distance
    if isNearZero (A + B + C + D):
        # printf ("yes point (p = %s) is on plane: A = %g, B = %g, C = %g, D = %g, A + B + C + D = %g\n",
        # p, A, B, C, D, A+B+C+D)
        pass
    else:
        printf ("no point (p = %s) is not on plane: A = %g, B = %g, C = %g, D = %g, A + B + C + D = %g\n",
                p, A, B, C, D, A+B+C+D)
    assert (isNearZero (A + B + C + D))


def verify_plane_points (vec, distance, f, polygon_points):
    for i in f:
        # printf ("vertice %d  %s\n", i, polygon_points[i])
        verify_point_on_plane (vec, distance, polygon_points[i])

#
#  roof - pos is the bottom left corner of the roof brick.
#         polygon_points is a list of quad points.  Each
#         quad point uses the format:
#         [ basepoint, vec0, vec1, vec2 ]
#         basepoint is a corner of the polygon
#         basepoint + vec0 is another corner of the polygon
#         basepoint + vec1 is another corner of the polygon
#         basepoint + vec2 is another corner of the polygon
#

def roof (o, polygon_points, faces, material, transform):
    verify_polygon_points (polygon_points, "calc_face")
    polygon_points = translatePoints (polygon_points)
    verify_polygon_points (polygon_points, "calc_face")
    for i, f in enumerate (faces):
        vec, distance = calc_face (polygon_points[f[0]], polygon_points[f[1]], polygon_points[f[2]])
        verify_plane_points (vec, distance, f, polygon_points)
        o = plane (o, vec, distance, material, transform, "")
    return o


#
#  translatePoly - translate and return a list of vertices.
#

def translatePoly (vertices):
    result = []
    for v in vertices:
        result += [translatePos (v)]
    return result


def polybrick (o, polygon_points, faces, material, transform):
    printf ("faces = %s\n", faces)
    printf ("vertices = %s\n", polygon_points)
    verify_polygon_points (polygon_points, "poly_brick_face before translate")
    polygon_points = translatePoly (polygon_points)
    verify_polygon_points (polygon_points, "poly_brick_face after translate")
    for i, f in enumerate (faces):
        printf ("face no %d  %s\n", i, f)
        vec, distance = calc_face (polygon_points[f[0]], polygon_points[f[1]], polygon_points[f[2]])
        verify_plane_points (vec, distance, f, polygon_points)
        o = plane (o, vec, distance, material, transform, "")
    return o


#
#  flushCuboids - flush all the cuboid bricks which have the same fixed
#                 value.
#

def flushCuboids (o, bcount, fixed):
    for k in list (cuboids.keys ()):
        b = cuboids[k]  # Python v2 and v3 compatible
        if b.fixed == fixed:
            if args.debug:
                print("cuboid", b.pos, "size", b.size)
            o.write ('    // cuboid ' + str (k) + '\n')
            o.write ('    {\n')
            o.write ('         brushDef3\n')
            o.write ('         {\n')
            o = brick (o, b.pos, b.end, b.material, b.transform)
            o.write ('         }\n')
            o.write ('    }\n')
            bcount += 1
    return o, bcount


#
#  flushRoofBricks - flush the roof bricks.
#

def flushRoofBricks (o, bcount):
    for k in list (roofBricks.keys ()):
        b = roofBricks[k]
        # print "roofbrick, polygon_points =", b.polygon_points, "material =", b.material
        o.write ('    // roof brick ' + str (k) + "\n")
        o.write ('    {\n')
        o.write ('         brushDef3\n')
        o.write ('         {\n')
        o = roof (o, b.polygon_points, b.faces, b.material, b.transform)
        o.write ('         }\n')
        o.write ('    }\n')
        bcount += 1
    return o, bcount


#
#  flushPolyObjects - flush the poly objects.
#

def flushPolyObjects (o, bcount):
    for k in list (polyobjs.keys ()):
        b = polyobjs[k]
        # sort_vertices ()
        vert = b.polygon_points
        faces = b.faces
        # print "roofbrick, polygon_points =", b.polygon_points, "material =", b.material
        o.write ('    // polygon object ' + str (k) + " " + b.name + "\n")
        o.write ('    {\n')
        o.write ('         brushDef3\n')
        o.write ('         {\n')
        o = polybrick (o, vert, faces, b.material, b.transform)
        o.write ('         }\n')
        o.write ('    }\n')
        bcount += 1
    return o, bcount


#
#  flushBricks - flushes all used fixed cuboids to the output file, o
#

def flushBricks (o, bcount):
    o, bcount = flushCuboids (o, bcount, True)
    o, bcount = flushRoofBricks (o, bcount)
    o, bcount = flushPolyObjects (o, bcount)
    return o, bcount


#
#  doWall - an entity, e, has the format [[x0, y0], [x1, y2], orientation, 'wall'].
#           Generate a series of small bricks which will be joined together later.
#

def doWall (r, e):
    global minFloor, maxFloor
    if isVertical (e):
        a = min (e[0][1], e[1][1])
        b = max (e[0][1], e[1][1])
        for l in range (a, b+1):
            pos = [e[0][0], l, minFloor-1]
            end = [e[1][0]+1, l+1, getFloorLevel (r) + maxz]
            size = subVec (end, pos)
            newcuboid (pos, size, e[-2], r)
    elif isHorizontal (e):
        a = min (e[0][0], e[1][0])
        b = max (e[0][0], e[1][0])
        for l in range (a, b+1):
            pos = [l, e[0][1], minFloor-1]
            end = [l+1, e[1][1]+1, getFloorLevel (r) + maxz]
            size = subVec (end, pos)
            newcuboid (pos, size, e[-2], r)


def brushHeader (o, e, description):
    o.write ('         brushDef3\n')
    o.write ('         {\n')
    if args.comments:
        o.write ('             ')
        o.write ("// " + str (e) + '\n')
    if args.debug:
        print(e)
    o.write ('             // ' + description + ' ' + str (e) + '\n')
    return o


def brushFooter (o):
    o.write ('         }\n')
    return o

#
#  generateStepsVerticalWall - generate a sequence of steps on a vertical wall.
#

def generateStepsVerticalWall (r, e, l):
    if args.debug:
        print("vertical steps in room", r, e)
    leftLevel  = rooms[str (getFloor (e[0][0]-1, e[0][1]))].floorLevel
    rightLevel = rooms[str (getFloor (e[0][0]+1, e[0][1]))].floorLevel
    winc = 1.0/float (noSteps)
    if leftLevel == rightLevel:
        hinc = 0
    else:
        hinc = floorStep
    if args.debug:
        print("rightLevel =", rightLevel, "leftLevel =", leftLevel, "winc =", winc, "hinc =", hinc)
    widthOffset = 0
    heightOffset = 0
    for s in range (noSteps):
        pos = [e[0][0]+widthOffset, l, minFloor-1]
        if args.debug:
            print(leftLevel, rightLevel, widthOffset, heightOffset)
        widthOffset += winc
        heightOffset += hinc
        if leftLevel < rightLevel:
            end = [e[1][0]+widthOffset, l+1, leftLevel + heightOffset]
        else:
            end = [e[1][0]+widthOffset, l+1, leftLevel - heightOffset + hinc]
        size = subVec (end, pos)
        newcuboid (pos, size, 'wall', r)


#
#  generateStepsHorizontalWall - generate a sequence of steps on a horizontal wall.
#

def generateStepsHorizontalWall (r, e, l):
    if args.debug:
        print("horizontal steps in room", r, e)
    botLevel = rooms[str (getFloor (e[0][0], e[0][1]-1))].floorLevel
    topLevel = rooms[str (getFloor (e[0][0], e[0][1]+1))].floorLevel
    winc = 1.0/float (noSteps)
    if topLevel == botLevel:
        hinc = 0
    else:
        hinc = floorStep
    widthOffset = 0
    heightOffset = 0
    for s in range (noSteps):
        pos = [l, e[0][1]+widthOffset, minFloor-1]
        widthOffset += winc
        heightOffset += hinc
        if botLevel < topLevel:
            end = [l+1, e[1][1]+widthOffset, botLevel + heightOffset]
        else:
            end = [l+1, e[1][1]+widthOffset, botLevel - heightOffset + hinc]
        size = subVec (end, pos)
        newcuboid (pos, size, 'wall', r)

#
#  generateBaseCoord - returns a list of the arch footprint
#                      at an angle and r0 away from the midpoint.
#

def generateBaseCoords (length, width, r0, angle):
    radians = Decimal ("%g" % angle) * Decimal (math.pi) / Decimal (180.0)
    x0 = 0
    y0 = math.cos (radians) * r0
    z0 = math.sin (radians) * r0
    x1 = width
    y1 = math.cos (radians) * (length + r0)
    z1 = math.sin (radians) * (length + r0)
    return [[x0, y0, z0], [x0, y1, z1], [x1, y1, z1], [x1, y0, z0]]


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
#
#
#  generate_cube_points - return the points and faces of a cube.
#                         The points returned will be in the order:
#                         [botpos, botpos+x, botpos+y, botpos+z,
#                          toppos, botpos-x, botpos-y, botpos-z]
#
#                         assuming botpos is the lowest left back corner
#                                  toppos is the highest right front corner

def createPolyArch (p):
    printf ("p = %s\n", p)
    points = [p[2], p[3], p[0], p[1],
              p[4], p[5], p[6], p[7]]
    #
    #  faces is a list of face.  Each faces is a list of points.
    #
    faces = [[2, 4, 3, 5],    #  front
             [1, 7, 2, 4],    #  right
             [3, 5, 0, 6],    #  left
             [6, 7, 0, 1],    #  back
             [5, 4, 6, 7],    #  top
             [3, 0, 2, 1]]    #  bottom
    printf ("faces = %s\n", faces)
    printf ("vertices = %s\n", points)
    for i, v in enumerate (points):
        printf ("%d %s\n", i, v)
    return points, faces

#
#  generateArchBrick - create an arch brick
#

def generateArchBrick (room, edgepos, midpos, angle0, angle1,
                       length, width, isVertical, direction):
    r0 = magnitude (subVec (edgepos, midpos))
    printf ("r0 = %g\n", r0)
    basefootprint = generateBaseCoords (length, width, r0, angle0)
    printf ("basefootprint = %s\n", basefootprint)
    basefootprint = multPolyVec (basefootprint, direction)
    printf ("basefootprint = %s\n", basefootprint)
    basecoords = addPolyVec (basefootprint, midpos)
    printf ("basecoords = %s\n", basecoords)
    topfootprint = generateBaseCoords (length, width, r0, angle1)
    printf ("topfootprint = %s\n", topfootprint)
    topfootprint = multPolyVec (topfootprint, direction)
    topcoords = addPolyVec (topfootprint, midpos)
    poly, faces = createPolyArch (basecoords + topcoords)
    addpolyobj (poly, faces, "plinth", room, "arch")


#
#  generateVerticalArch
#

def generateVerticalArch (room, entity, miny, maxy):
    floorLevel = getFloorLevel (room)
    xpos = entity[0][0]
    #
    #  arch pillar on the miny side of the archway
    #
    straightEdgePos = [xpos, miny, floorLevel]
    height = 0
    for xyoffset, zoffset in [[archBase, archBaseHeight],
                              [archReduction, archMidHeight],
                              [archReduction2, minDoorHeight / 1.6 * inchesPerUnit - archMidHeight - archBaseHeight - archTopHeight],
                              [archReduction, archMidHeight],
                              [archTop, archTopHeight]]:
        pos = subVec (straightEdgePos, [xyoffset / inchesPerUnit,
                                        xyoffset / inchesPerUnit,
                                        0])
        pos = addVec (pos, [0, 0, height])
        size = [xyoffset / inchesPerUnit,
                xyoffset / inchesPerUnit,
                zoffset  / inchesPerUnit]
        print ("archway, pos =", pos, "size =", size)
        newcuboid (pos, size, 'plinth', room)
        height += zoffset / inchesPerUnit

    #
    #  arch pillar on the maxy side of the archway
    #
    straightEdgePos = [xpos, maxy + 1, floorLevel]
    height = 0
    for xyoffset, zoffset in [[archBase, archBaseHeight],
                              [archReduction, archMidHeight],
                              [archReduction2, minDoorHeight / 1.6 * inchesPerUnit - archMidHeight - archBaseHeight - archTopHeight],
                              [archReduction, archMidHeight],
                              [archTop, archTopHeight]]:
        pos = subVec (straightEdgePos, [xyoffset / inchesPerUnit, 0, 0])
        pos = addVec (pos, [0, 0, height])
        size = [xyoffset / inchesPerUnit,
                xyoffset / inchesPerUnit,
                zoffset  / inchesPerUnit]
        print ("archway, pos =", pos, "size =", size)
        newcuboid (pos, size, 'plinth', room)
        height += zoffset / inchesPerUnit
    #
    #  arch on miny
    #
    straightEdgePos = [xpos, miny, floorLevel]
    straightEdgePos = addVec (straightEdgePos, [0, 0, .5])  ## --fixme--
    printf ("straightEdgePos = %s\n", straightEdgePos)
    angleIncLength = [[archBaseAngle, archBlockBase / inchesPerUnit]]
    printf ("angleIncLength = %s\n", angleIncLength)
    angle = archBaseAngle
    while angle < 90 - archCapAngle / 2:
        angle += archBlockAngle
        angleIncLength += [[archBlockAngle, archSegmentBase / inchesPerUnit]]
    angleIncLength += [[archCapAngle, archBlockBase / inchesPerUnit]]
    angle += archCapAngle
    while angle < 180 - archCapAngle:
        angle += archBlockAngle
        angleIncLength += [[archBlockAngle, archSegmentBase / inchesPerUnit]]
    angleIncLength += [[archCapAngle, archBlockBase / inchesPerUnit]]
    # angleIncLength = [angleIncLength[1]]
    printf ("angleIncLength = %s\n", angleIncLength)
    angle = 0
    # pos = addVec (straightEdgePos, [0, 0, height])
    for inc, length in angleIncLength:
        pos = subVec (straightEdgePos, [length + 1, 1, 0])
        printf ("pos = %s\n", pos)
        midpos = addVec (pos, [0, (maxy + 1 - miny) / 2, 0])
        printf ("midpos = %s\n", midpos)
        printf ("angle = %g, length = %g\n", angle, length)
        generateArchBrick (room, pos, midpos, angle, angle + inc,
                           length, length, True, [1, -1, 1])
        angle += inc
    # and the cap stone
    print ("angle =", angle)
    # addpolyobj (prevBase1 + prevBase2, faces, "plinth", room)


#
#  generateVerticalArch2
#

def generateVerticalArch2 (room, entity, miny, maxy):
    floorLevel = getFloorLevel (room)
    xpos = entity[0][0]
    #
    #  arch pillar on the miny side of the archway
    #
    straightEdgePosMin = [xpos, miny, floorLevel]
    height = 0
    #
    #  create the minpillar at the origin
    #
    minpillar = []
    for xyoffset, zoffset in [[archBase, archBaseHeight],
                              [archReduction, archMidHeight],
                              [archReduction2, minDoorHeight / 1.6 * inchesPerUnit - archMidHeight - archBaseHeight - archTopHeight],
                              [archReduction, archMidHeight],
                              [archTop, archTopHeight]]:
        brick = poly ().unit_cube ().set_texture ('all', 'plinth')
        pos = subVec (straightEdgePosMin, [xyoffset / inchesPerUnit,
                                           xyoffset / inchesPerUnit,
                                           0])
        pos = addVec (pos, [0, 0, height])
        size = [xyoffset / inchesPerUnit,
                xyoffset / inchesPerUnit,
                zoffset  / inchesPerUnit,
                0]
        print (pos)
        brick = brick.scale (size).translate (pos)
        minpillar += [brick]
        height += zoffset / inchesPerUnit
    #
    #  create the maxpillar using the minpillar and translating it.
    #
    maxpillar = []
    straightEdgePosMax = [xpos, maxy, floorLevel]
    for brick in minpillar:
        maxpillar += [brick.copy.reflect_x ().translate (straightEdgePosMax)]
    c = []
    #
    #  finally move the minpillar into the correct position.
    #
    for brick in minpillar:
        c += [brick.copy.translate (straightEdgePosMin)]
    minpillar = c
    for obj in minpillar + maxpillar:
        addpolyobj (obj.get_vertices (),
                    obj.get_faces (),
                    obj.get_texture ('top'),
                    room,
                    'pillar')


#
#  staircase
#

"""
def staircase (room, pos, height, r0, r1, increment, angle):
    floor_level = get_floor_level (room)
    stair_level_offset = 0
    stair_angle = 0
    while stair_level_offset < height:
        newstair (room, pos, r0, r1, increment,
                  angle, stair_angle, stair_level_offset)
        stair_angle += angle
        stair_level_offset += increment
"""


#
#  doOpen - create an open door.
#

def doOpen (r, e):
    global minFloor, maxFloor
    if args.debug:
        print("building floor and ceiling for doorway")
    if (e[-1] == 'left') or (e[-1] == 'right'):
        #
        #  vertical door (on the 2D map)
        #
        a = min (e[0][1], e[1][1])  # smallest y coord
        b = max (e[0][1], e[1][1])  # largest y coord
        for l in range (a, b+1):    # iterative over all y coords
            generateStepsVerticalWall (r, e, l)  # build the steps
            #
            #  now build the ceiling over the doorway
            #
            h = minDoorHeight + getFloorLevel (r)
            pos = [e[0][0], l, h]   # bottom left
            end = [e[1][0]+1, l+1, maxz + getFloorLevel (r)]  # top right
            size = subVec (end, pos)  #  size of ceiling
            if args.debug:
                print("vertical ceiling block at", pos, end, size)
            newcuboid (pos, size, 'wall', r)   # ceiling
            if args.visportals:
                # visportal doorway
                #
                # fill in the doorway with visportal block
                #
                # vertical visportal code
                pos = [e[0][0], l, rooms[r].floorLevel]
                end = [e[1][0]+1, l+1, minCeilingHeight]
                size = subVec (end, pos)
                newcuboid (pos, size, e[-2], r)
        generateVerticalArch (r, e, a, b)  ### old orig arch code
        # generateVerticalArch2 (r, e, a, b)
    else:
        #
        #  horizontal door (on the 2D map)
        #
        a = min (e[0][0], e[1][0])
        b = max (e[0][0], e[1][0])
        for l in range (a, b+1):
            generateStepsHorizontalWall (r, e, l)
            h = minCeilingHeight
            h = minDoorHeight + getFloorLevel (r)
            pos = [l, e[0][1], h]
            end = [l+1, e[1][1]+1, maxz + getFloorLevel (r)]
            size = subVec (end, pos)
            if args.debug:
                print("horiz ceiling block at", pos, end, size)
            newcuboid (pos, size, 'wall', r)   # ceiling
            if args.visportals:
                # visportal doorway
                #
                # fill in the doorway with visportal block
                #
                # horizontal visportal doorway
                pos = [l, e[0][1], rooms[r].floorLevel]
                end = [l+1, e[1][1]+1, minCeilingHeight]
                size = subVec (end, pos)
                newcuboid (pos, size, e[-2], r)



def buildVerticalBrickWall (xaxis, miny, maxy, minz, maxz, roomNo):
    xpos = float (xaxis) + brickMidOffset
    length = maxy - miny
    height = maxz - minz
    totalRows = int (height / brickHeight)
    totalRows = 4
    x = xpos
    z = minz
    # print ("totalRows =", totalRows)
    # print ("no brick =", int (length / brickLength))
    for row in range (totalRows):
        y = maxy
        # print ("length =", length, length/brickLength)
        pos = [xaxis, y+beamSupportSize, z]
        size = [1.0, beamSupportSize, brickHeight]
        newcuboid (pos, size, "wall", roomNo)
        y -= beamSupportSize
        for brick in range (int (length / brickLength)):
            pos = [x, y, z]
            size = [brickWidth, brickLength, brickHeight]
            newcuboid (pos, size, "secret", roomNo, False, False)
            y -= brickLength
        pos = [xaxis, y+beamSupportSize, z]
        size = [1.0, beamSupportSize, brickHeight]
        newcuboid (pos, size, "wall", roomNo)
        y -= beamSupportSize
        z += brickHeight
    for y in range (miny, maxy + 1):
        pos = [xaxis, y, z]
        size = [1, 1, 0.5]
        newcuboid (pos, size, secretDoorLintal, roomNo)  # beam lintel
    z += 0.5
    for y in range (miny, maxy + 1):
        pos = [xaxis, y, z]
        size = [1, 1, 0.5]
        newcuboid (pos, size, "wall", roomNo)
    z += 0.5
    for z in range (int (z), int (getFloorLevel (roomNo) + minCeilingHeight) + 1):
        for y in range (miny, maxy + 1):
            pos = [xaxis, y, z]
            size = [1, 1, 1]
            newcuboid (pos, size, "wall", roomNo)


def buildHorizBrickWall (yaxis, minx, maxx, minz, maxz, roomNo):
    ypos = float (yaxis) + brickMidOffset
    length = maxx - minx
    height = maxz - minz
    totalRows = int (height / brickHeight)
    totalRows = 4
    y = ypos
    z = minz
    # print ("totalRows =", totalRows)
    # print ("no brick =", int (length / brickLength))
    for row in range (totalRows):
        x = maxx
        # print ("length =", length, length/brickLength)
        pos = [x+beamSupportSize, yaxis, z]
        size = [beamSupportSize, 1.0, brickHeight]
        newcuboid (pos, size, "wall", roomNo)
        x -= beamSupportSize
        for brick in range (int (length / brickLength)):
            pos = [x, y, z]
            size = [brickLength, brickWidth, brickHeight]
            newcuboid (pos, size, "secret", roomNo, False, False)
            x -= brickLength
        pos = [x+beamSupportSize, yaxis, z]
        size = [beamSupportSize, 1.0, brickHeight]
        newcuboid (pos, size, "wall", roomNo)
        x -= beamSupportSize
        z += brickHeight
    for x in range (minx, maxx + 1):
        pos = [x, yaxis, z]
        size = [1, 1, 0.5]
        newcuboid (pos, size, secretDoorLintal, roomNo)
    z += 0.5
    for x in range (minx, maxx + 1):
        pos = [x, yaxis, z]
        size = [1, 1, 0.5]
        newcuboid (pos, size, "wall", roomNo)
    z += 0.5
    for z in range (int (z), int (getFloorLevel (roomNo) + minCeilingHeight) + 1):
        for x in range (minx, maxx + 1):
            pos = [x, yaxis, z]
            size = [1, 1, 1]
            newcuboid (pos, size, "wall", roomNo)


#
#  calcBrickOrigin - return the mid point in a brick.
#

def calcBrickOrigin (brick):
    # print ("minx =", minx, "miny =", miny)
    start = subVec (brick.pos, [minx, miny, 0])
    start = addVec (brick.pos, [0, 0, -brickHeight])
    # print ("start =", start)
    # print ("brick.size =", brick.size)
    end = addVec (start, brick.size)
    # print ("end =", end)
    mid = [((start[0] + end[0])/2),
           ((start[1] + end[1])/2),
           ((start[2] + end[2])/2)]
    # print ("mid =", mid)
    mid = vecInches (end)
    # print ("  mid =", mid)
    mid = toIntList (mid)
    # print ("  final mid =", mid)
    return mid[0], mid[1], -mid[2]


#
#  doSecret - create a secret door.
#

def doSecret (roomNo, e):
    global minFloor, maxFloor
    if args.debug:
        print ("secret door, building floor and ceiling for doorway")
    if (e[-1] == 'left') or (e[-1] == 'right'):
        #
        #  vertical door (on the 2D map)
        #
        miny = min (e[0][1], e[1][1])  # smallest y coord
        maxy = max (e[0][1], e[1][1])  # largest y coord
        for y in range (miny, maxy+1): # iterative over all y coords
            generateStepsVerticalWall (roomNo, e, y)  # build the steps
            #
            #  now build the ceiling over the doorway
            #
            h = minDoorHeight + getFloorLevel (roomNo)
            pos = [e[0][0], y, h]   # bottom left
            end = [e[1][0]+1, y+1, maxz + getFloorLevel (roomNo)]  # top right
            size = subVec (end, pos)  #  size of ceiling
            if args.debug:
                print("vertical ceiling block at", pos, end, size)
            newcuboid (pos, size, 'wall', roomNo)   # ceiling

        # fill in the doorway with moveable bricks
        # pos = [e[0][0], y, rooms[roomNo].floorLevel]
        # end = [e[1][0]+1, y+1, minCeilingHeight]
        # size = subVec (end, pos)
        buildVerticalBrickWall (e[0][0], miny, maxy, getFloorLevel (roomNo), h, roomNo)
    else:
        #
        #  horizontal door (on the 2D map)
        #
        minx = min (e[0][0], e[1][0])  # smallest x coord
        maxx = max (e[0][0], e[1][0])  # largest x coord
        for x in range (minx, maxx+1): # iterate over all x coords of the door
            generateStepsHorizontalWall (roomNo, e, x)
            h = minDoorHeight + getFloorLevel (roomNo)
            pos = [x, e[0][1], h]
            end = [x+1, e[1][1]+1, maxz + getFloorLevel (roomNo)]
            size = subVec (end, pos)
            if args.debug:
                print("horiz ceiling block at", pos, end, size)
            newcuboid (pos, size, 'wall', roomNo)   # ceiling
        buildHorizBrickWall (e[0][1], minx, maxx, getFloorLevel (roomNo), h, roomNo)


brickFunc = {'leftwall':doWall,
             'topwall':doWall,
             'rightwall':doWall,
             'bottomwall':doWall,
             'leftopen': doOpen,
             'rightopen': doOpen,
             'topopen':doOpen,
             'bottomopen':doOpen,
             'leftsecret': doSecret,
             'rightsecret': doSecret,
             'topsecret':doSecret,
             'bottomsecret':doSecret}


#
#  generateKey - return a textual key for the entity.
#

def generateKey (e):
    return "%s %d% d %d %d" % (e[-2], e[0][0], e[0][1], e[1][0], e[1][1])


#
#  alreadyBuilt - return True if this entity has already been built
#                 (This will occur for doors as each room knows about
#                  the same door).
#

def alreadyBuilt (e):
    global brushes
    if e[-2] == 'wall':
        return False
    return generateKey (e) in brushes


#
#  setBuild - record that we have built, e.
#

def setBuilt (e):
    global brushes
    brushes[generateKey (e)] = True


#
#  generateBricks - convert a pen wall into a sequence of bricks (cuboids).
#

def generateBricks (r, e):
    if args.debug:
        print("room", r, e, end=' ')
    if brickFunc[e[-1]+e[-2]] == None:
        warning ("do not know how to build " + str (e) + " in room " + r)
    #
    # doorways are known about from both rooms, but we only need to build it once
    #
    if alreadyBuilt (e):
        if args.debug:
            print("aready built")
    else:
        brickFunc[e[-1]+e[-2]] (r, e)
    setBuilt (e)


#
#  generateBrushes - each wall is made up from a single entity.
#                    Each entity will have 6 faces for a building block.
#

def generateBrushes (r, e, o, bcount):
    if args.debug:
        print("room", r, e, end=' ')
    if entityFunc[e[-1]+e[-2]] == None:
        warning ("do not know how to build brush" + str (e) + "in room " + r)
        return o, bcount
    if alreadyBuilt (e):
        if args.debug:
            print("aready built")
        return o, bcount
    if args.debug:
        print("building")
    o.write ('    // primitive ' + str (bcount) + '\n')
    o.write ('    {\n')
    o, bcount = entityFunc[e[-1]+e[-2]] (r, e, o, bcount)
    o.write ('    }\n')
    setBrushBuilt (e)
    return o, bcount


def getMinMax (minx, miny, maxx, maxy, e):
    if minx == None:
        minx = min (int (e[0][0]), int (e[1][0]))
    else:
        minx = min (int (e[0][0]), minx)
    if maxx == None:
        maxx = max (int (e[0][0]), int (e[1][0]))
    else:
        maxx = max (int (e[0][0]), maxx)
    if miny == None:
        miny = min (int (e[0][1]), int (e[1][1]))
    else:
        miny = min (int (e[0][1]), miny)
    if maxy == None:
        maxy = max (int (e[0][1]), int (e[1][1]))
    else:
        maxy = max (int (e[0][1]), maxy)
    return minx, miny, maxx, maxy


#
#  findMinMax - return a list of two positions which determine the min/max for the x/y position.
#               Ie:  return [[minx, miny], [maxx, maxy]]
#

def findMinMax (r):
    minx, miny, maxx, maxy = None, None, None, None
    for e in rooms[r].walls:
        minx, miny, maxx, maxy = getMinMax (minx, miny, maxx, maxy, e)
    return [[minx, miny], [maxx, maxy]]


def sortMinMax (a, b):
    if a > b:
        return b, a
    return a, b


#
#  findOffsetInRoom - scans room, r, for the minx, miny, minz, maxz values.
#

def findOffsetInRoom (r):
    global minx, miny, minz, maxx, maxy, maxz
    for e in rooms[r].walls:
        if minx == None:
            minx = int (e[0][0])
        else:
            minx = min (int (e[0][0]), minx)
        if miny == None:
            miny = int (e[0][1])
        else:
            miny = min (miny, int (e[0][1]))
        if minz == None:
            minz = rooms[r].floorLevel-2
        else:
            minz = min (rooms[r].floorLevel-2, minz)
        if maxx == None:
            maxx = int (e[1][0])
        else:
            maxx = max (int (e[1][0]), maxx)
        if maxy == None:
            maxy = int (e[1][1])
        else:
            maxy = max (maxy, int (e[1][1]))
        if maxz == None:
            maxz = rooms[r].floorLevel + minCeilingHeight + 1
        else:
            maxz = max (rooms[r].floorLevel + minCeilingHeight + 1, maxz)


#
#   findOffsets - determine the minx, miny, minz in the complete map.
#

def findOffsets ():
    global minvec
    for r in list(rooms.keys ()):
        findOffsetInRoom (r)
    minvec = [minx, miny, minz]


#
#  initRoomFloor -
#

def initRoomFloor ():
    initFloor (maxx, maxy, emptyValue)
    for r in list(rooms.keys ()):
        for w in rooms[r].walls:
            plotLine (w, wallValue)
        if rooms[r].inside == None:
            error ('room %d must have an inside position', int (r))
        else:
            floodFloor (int (r), intVec (rooms[r].inside))
    if args.debug:
        for f in floor:
            print(f)

def candleCeil (r, x, y, z):
    pos = [x, y, z]
    size = [0.5, 0.5, 0.0]
    col = scopeColourRoom (r, "CEIL")
    newlight (pos, size, light (col, "CEIL", r))


def candleStair (r, x, y, z):
    pos = [x, y, z]
    size = [0.0, 0.0, 0.0]
    col = scopeColourRoom (r, "FLOOR")
    newlight (pos, size, light (col, "FLOOR", r))


def candle (r, x, y):
    candleCeil (r, x, y, candleHeight)


def beamSupport (r, x, y, h):
    pos = [x, y, h]
    size = [beamSupportSize, beamSupportSize, beamSupportSize]
    newcuboid (pos, size, 'wall', r)


def beamTransim (r, botpos, toppos, translate_top):
    points, faces = generate_roof_points (botpos, toppos, translate_top)
    addroofbrick (points, faces, "beam", r)   # facing up 2D when viewed from top


def makeBeamX (r, x, y0, y1):
    h = getFloorLevel (r) + minCeilingHeight - 0.5
    if args.debug:
        print("beamX", x, y0, y1, h)
    #
    #  main flat, support beam
    #
    for y in range (y0+1, y1):
        pos = [x, y, h]
        size = [0.5, 1.0, 0.5]
        if args.debug:
            print("beamX block", x, y, h)
        newcuboid (pos, size, 'beam', r)
    h = getFloorLevel (r) + minCeilingHeight
    #
    #  A shape support (right)
    #
    roof_height = float (y1-y0+1)/2.0
    botpos = [x,
              y0 + 1.0,
              h]
    toppos = [x + 0.5,
              y0 + 1.5,
              h + roof_height]
    translate_top = [0.0, roof_height-1.0, 0.0]
    beamTransim (r, botpos, toppos, translate_top)
    #
    #  A shape support (left)
    #
    roof_height = float (y1-y0+1)/2.0
    botpos = [x,
              y1-0.5,
              h]
    toppos = [x + 0.5,
              y1,
              h + roof_height]
    translate_top = [0.0, -(roof_height-1.0), 0.0]
    beamTransim (r, botpos, toppos, translate_top)

    #
    #  mid pillar
    #
    roof_height = float (y1-y0+1)/2.0
    botpos = [x + 0.125,
              y0 + roof_height + 0.125,
              h]
    toppos = [x + 0.5 - 0.125,
              y0 + roof_height - 0.125,
              h + roof_height]
    translate_top = [0, 0, 0]
    beamTransim (r, botpos, toppos, translate_top)

    #
    #  brace (left)
    #
    roof_height = float (y1-y0+1)/2.0
    botpos = [x + 0.125,
              y0 + roof_height + 0.125,
              h]
    toppos = [x + 0.5 - 0.125,
              y0 + roof_height - 0.125,
              h + roof_height/2.0]
    translate_top = [0, roof_height/2.0, 0]
    beamTransim (r, botpos, toppos, translate_top)

    #
    #  brace (right)
    #
    roof_height = float (y1-y0+1)/2.0
    botpos = [x + 0.125,
              y0 + roof_height + 0.125,
              h]
    toppos = [x + 0.5 - 0.125,
              y0 + roof_height - 0.125,
              h + roof_height/2.0]
    translate_top = [0, -roof_height/2.0, 0]
    beamTransim (r, botpos, toppos, translate_top)

    #
    #  stone support for the beam
    #
    beamSupport (r, x, y0+1.0, h-1.0)
    beamSupport (r, x, y1-0.5, h-1.0)


def makeBeamY (r, x0, x1, y):
    h = getFloorLevel (r) + minCeilingHeight - 0.5
    if args.debug:
        print("beamY", x0, x1, y, h)
    #
    #  main flat, support beam
    #
    for x in range (x0+1, x1):
        pos = [x, y, h]
        size = [1.0, 0.5, 0.5]
        if args.debug:
            print("beamY block", x, y, h)
        newcuboid (pos, size, 'beam', r)
    #
    #  A shape support (right)
    #
    h = getFloorLevel (r) + minCeilingHeight
    roof_height = float (x1-x0+1)/2.0
    botpos = [x0 + 1.0,
              y,
              h]
    toppos = [x0 + 1.5,
              y + 0.5,
              h + roof_height]
    translate_top = [roof_height-1.0, 0.0, 0.0]
    beamTransim (r, botpos, toppos, translate_top)

    #
    #  A shape support (left)
    #
    roof_height = float (x1-x0+1)/2.0
    botpos = [x1 - 0.5,
              y,
              h]
    toppos = [x1,
              y + 0.5,
              h + roof_height]
    translate_top = [- (roof_height-1.0), 0.0, 0.0]
    beamTransim (r, botpos, toppos, translate_top)

    #
    #  mid pillar
    #
    roof_height = float (x1-x0+1)/2.0
    botpos = [x0 + roof_height + 0.125,
              y + 0.125,
              h]
    toppos = [x0 + roof_height - 0.125,
              y + 0.5 - 0.125,
              h + roof_height]
    translate_top = [0, 0, 0]
    beamTransim (r, botpos, toppos, translate_top)
    #
    #  brace (left)
    #
    roof_height = float (x1-x0+1)/2.0
    botpos = [x0 + roof_height + 0.125,
              y + 0.125,
              h]
    toppos = [x0 + roof_height - 0.125,
              y + 0.5 - 0.125,
              h + roof_height/2.0]
    translate_top = [roof_height/2.0, 0, 0]
    beamTransim (r, botpos, toppos, translate_top)

    #
    #  brace (right)
    #
    roof_height = float (x1-x0+1)/2.0
    botpos = [x0 + roof_height + 0.125,
              y + 0.125,
              h]
    toppos = [x0 + roof_height - 0.125,
              y + 0.5 - 0.125,
              h + roof_height/2.0]
    translate_top = [-roof_height/2.0, 0, 0]
    beamTransim (r, botpos, toppos, translate_top)

    #
    #  stone support for the beam
    #

    beamSupport (r, x0+1.0, y, h-1.0)
    beamSupport (r, x1-0.5, y, h-1.0)


def makeCandleXapex (r, x, y0, y1):
    if args.candlelights and (y1 - y0 > 8):
        mid = (y0 + y1) / 2
        candleCeil (r, x, mid, candleHeight + mid -y0 -1)
        quarter = (y0 + y1) / 4 - y0
        # candleCeil (r, x, y0 + quarter, candleHeight + quarter)
        # candleCeil (r, x, y0 + 3 * quarter, candleHeight + quarter)


def makeCandleYapex (r, x0, x1, y):
    if args.candlelights and (x1 - x0 > 8):
        mid = (x0 + x1) / 2
        candleCeil (r, mid, y, candleHeight + mid -x0 -1)
        quarter = (x0 + x1) / 4 - x0
        # candleCeil (r, x0 + quarter, y, candleHeight + quarter)
        # candleCeil (r, x0 + 3 * quarter, y, candleHeight + quarter)


def makeCandleX (r, x, y0, y1):
    if args.candlelights:
        candle (r, x, y0+1.0)
        candle (r, x, y1-0.5)
        if y1 - y0 > 8:
            mid = int ((y1 - y0) / 2)
            for y in range (4, mid, 4):
                candle (r, x, y0+1.0+y)
                candle (r, x, y1-0.5-y)


def makeCandleY (r, x0, x1, y):
    if args.candlelights:
        candle (r, x0+1.0, y)
        candle (r, x1-0.5, y)
        if x1 - x0 > 8:
            mid = int ((x1 - x0) / 2)
            for x in range (4, mid, 4):
                candle (r, x0+1.0+x, y)
                candle (r, x1-0.5-x, y)

#
#  inBetween - return True if c lies between, a, and, b.
#

def inBetween (c, a, b):
    a = min (a, b)
    b = max (a, b)
    return (c >= a) and (c <= b)


#
#  onDoor - return True if point, x, y, is on a door in room, r.
#

def onDoor (x, y):
    if args.debug:
        print("is", x, y, "on a door")
    for r in list(rooms.keys ()):
        for d in rooms[r].doors:
            coords = d[0]
            if coords[0][0] == coords[1][0]:
                # vertical
                if (x == coords[0][0]) and inBetween (y, coords[0][1], coords[1][1]):
                    if args.debug:
                        print("yes")
                    return True
            else:
                # horizontal
                if (y == coords[0][1]) and inBetween (x, coords[0][0], coords[1][0]):
                    if args.debug:
                        print("yes")
                    return True
    if args.debug:
        print("no")
    return False


#
#  generateBeams - generate beams and light for 4 sided rooms.
#

def generateBeams (r, e):
    if len (rooms[r].walls) == 4:
        if args.debug:
            print("room", r, "beams being created")
        p = findMinMax (r)
        w0, w1 = None, None
        if args.debug:
            print(r, p)
            print(rooms[r].walls)
        x0, y0 = p[0]
        x1, y1 = p[1]
        if args.debug:
            print("x0, y0 =", x0, y0)
            print("x1, y1 =", x1, y1)
        if abs (x0-x1) > abs (y0-y1):
            # horizontal corridor, therefore create vertical beams
            # find the horiziontal walls
            for w in rooms[r].walls:
                if isHorizontal (w):
                    if w0 is None:
                        w0 = sortWall (w)
                    elif w1 is None:
                        w1 = sortWall (w)
            y0 = min (w0[0][1], w1[0][1])
            y1 = max (w0[0][1], w1[0][1])
            if args.debug:
                print(w0, w1)
            for x in range (w0[0][0]+1, w0[1][0], 4):
                if (not onDoor (x, y0)) and (not onDoor (x, y1)):
                    makeBeamX (r, x, y0, y1)
            for x in range (w0[0][0]+3, w0[1][0], 4):
                if (not onDoor (x, y0)) and (not onDoor (x, y1)):
                    makeCandleX (r, x, y0, y1)
            for x in range (w0[0][0]+2, w0[1][0], 4):
                makeCandleXapex (r, x, y0, y1)
        else:
            # vertical corridor, therefore create horizontal beams
            # find the vertical walls
            for w in rooms[r].walls:
                if isVertical (w):
                    if w0 is None:
                        w0 = sortWall (w)
                    elif w1 is None:
                        w1 = sortWall (w)
            x0 = min (w0[0][0], w1[0][0])
            x1 = max (w0[0][0], w1[0][0])
            if args.debug:
                print(w0, w1)
            for y in range (w0[0][1]+1, w0[1][1], 4):
                if (not onDoor (x0, y)) and (not onDoor (x1, y)):
                    makeBeamY (r, x0, x1, y)
            for y in range (w0[0][1]+3, w0[1][1], 4):
                if (not onDoor (x0, y)) and (not onDoor (x1, y)):
                    makeCandleY (r, x0, x1, y)
            for y in range (w0[0][1]+2, w0[1][1], 4):
                makeCandleYapex (r, x0, x1, y)


#
#  generateFlatCeiling - generate a simple flat surface (slab) at
#                        rooms[roomNo].floorLevel+minCeilingHeight .. minCeilingHeight
#                        on the Z axis.
#

def generateFlatCeiling (roomNo, e):
    for x in range (1, maxx):
        for y in range (1, maxy):
            if getFloor (x, y) == int (roomNo):
                pos = [x, y, getFloorLevel (roomNo) + minCeilingHeight]
                end = [x+1, y+1, getFloorLevel (roomNo) + minCeilingHeight + 1.0]
                size = subVec (end, pos)
                newcuboid (pos, size, 'ceiling', roomNo)


def apply_translate_top (points, translate_top, z_value):
    if args.debug:
        print("z_value =", z_value)
        print("before", points)
    translated = []
    for p in points:
        if p[2] == z_value:
            if args.debug:
                print("translating", translate_top)
            translated += [addVec (p, translate_top)]
        else:
            translated += [p]
    if args.debug:
        print("after", translated)
    return translated

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
#
#
#  generate_cube_points - return the points and faces of a cube.
#                         The points returned will be in the order:
#                         [botpos, botpos+x, botpos+y, botpos+z,
#                          toppos, botpos-x, botpos-y, botpos-z]
#
#                         assuming botpos is the lowest left back corner
#                                  toppos is the highest right front corner
#

def generate_cube_points (botpos, toppos):
    size = subVec (toppos, botpos)
    points = [botpos,
              addVec (botpos, [0, size[1], 0]),
              addVec (botpos, [size[0], size[1], 0]),
              addVec (botpos, [size[0], 0, 0]),
              toppos,
              subVec (toppos, [0, size[1], 0]),
              subVec (toppos, [size[0], size[1], 0]),
              subVec (toppos, [size[0], 0, 0])]
    #
    #  faces is a list of face.  Each faces is a list of points.
    #
    faces = [[2, 4, 3, 5],    #  front
             [1, 7, 2, 4],    #  right
             [3, 5, 0, 6],    #  left
             [6, 7, 0, 1],    #  back
             [5, 4, 6, 7],    #  top
             [3, 0, 2, 1]]    #  bottom
    return points, faces


#
#  generate_roof_points - returns a list of points and faces containing
#                         the roof brick.
#

def generate_roof_points (botpos, toppos, translate_top):
    botpos = translatePos (botpos)
    toppos = translatePos (toppos)
    botpos, toppos = reorderVertices (botpos, toppos)
    points, faces = generate_cube_points (botpos, toppos)
    if args.debug:
        print("cuboid roof =", points)
    points = apply_translate_top (points, translate_top, botpos[2])
    if args.debug:
        print("slanted roof =", points)
    return points, faces


def generatePitchedCeiling (r, e):
    if args.debug:
        print("generatePitchedCeiling")
    if len (rooms[r].walls) == 4:
        p = findMinMax (r)
        x0, y0 = p[0]
        x1, y1 = p[1]
        if args.debug:
            print("simple room", r, "coords", x0, y0, x1, y1)
        h = getFloorLevel (r) + minCeilingHeight
        if abs (x0-x1) > abs (y0-y1):
            x0, x1 = sortMinMax (x0, x1)
            y0, y1 = sortMinMax (y0, y1)
            if args.debug:
                print("horizontal")
            # horizontal corridor, therefore create vertical pitched ceiling
            roof_width = (y1-y0) / 2
            roof_height = (roof_width) + 1
            botpos = [x0+1, y0, h]
            toppos = [x1  , y0+1, h + roof_height]
            translate_top = [0, roof_width, 0]
            # translate_top = [0, 0, 1]
            # translate_top = [0, 0, 0]
            points, faces = generate_roof_points (botpos, toppos, translate_top)
            addroofbrick (points, faces, "ceiling", r)    # facing up 2D when viewed from top

            botpos = [x0+1 , y1, h]
            toppos = [x1, y1+1, h + roof_height]
            translate_top = [0, -roof_width, 0]
            # translate_top = [0, 0, 1]
            # translate_top = [0, 0, 0]
            points, faces = generate_roof_points (botpos, toppos, translate_top)
            addroofbrick (points, faces, "ceiling", r)  # facing up 2D when viewed from top

            # create gable ends
            pos = [x0, y0, h]
            end = [x0+1, y1+1, h + roof_height]
            size = subVec (end, pos)
            newcuboid (pos, size, "wall", r)
            pos = [x1, y0, h]
            newcuboid (pos, size, "wall", r)
        else:
            if args.debug:
                print("vertical")
            # vertical corridor, therefore create horizontal pitched ceiling
            x0, x1 = sortMinMax (x0, x1)
            y0, y1 = sortMinMax (y0, y1)

            roof_width = (x1-x0) / 2
            roof_height = (roof_width) + 1
            botpos = [x0  , y0+1, h]
            toppos = [x0+1, y1  , h + roof_height]
            translate_top = [roof_width, 0, 0]
            points, faces = generate_roof_points (botpos, toppos, translate_top)
            addroofbrick (points, faces, "ceiling", r)  # facing up 2D when viewed from top

            botpos = [x1, y0 + 1, h]
            toppos = [x1 + 1, y1, h + roof_height]
            translate_top = [-roof_width, 0, 0]
            points, faces = generate_roof_points (botpos, toppos, translate_top)
            addroofbrick (points, faces, "ceiling", r)  # facing up 2D when viewed from top

            # create gable ends
            pos = [x0, y0, h]
            end = [x1+1, y0+1, h + roof_height]
            size = subVec (end, pos)
            newcuboid (pos, size, "wall", r)
            pos = [x0, y1, h]
            newcuboid (pos, size, "wall", r)


def testFaces (r):
    global cuboidno, cuboids
    cuboidno = 1          #  total number of cuboids used.
    cuboids = {}
    if False:
        pos = [1, 1, 1]
        end = [2, 2, 2]
        size = subVec (end, pos)
        newcuboid (pos, size, "wall", r)
    else:
        botpos = [2, 2, 2]
        toppos = [20, 20, 20]
        translate_top = [0, 0, 0]
        points, faces = generate_roof_points (botpos, toppos, translate_top)
        # print("test points =", points)
        # print("test faces  =", faces)
        addroofbrick (points, faces, "ceiling", r)  # facing up 2D when viewed from top


def generateCeiling (roomNo, e):
    if (len (rooms[roomNo].walls) == 4) and args.pitch:
        generatePitchedCeiling (roomNo, e)
    else:
        generateFlatCeiling (roomNo, e)
    if args.autobeams:
        generateBeams (roomNo, e)


def generateFloor (r, e):
    global minFloor, maxFloor
    for x in range (1, maxx):
        for y in range (1, maxy):
            if getFloor (x, y) == int (r):
                pos = [x, y, minFloor-1]
                size = [1, 1, rooms[r].floorLevel-minFloor+1]
                if args.debug:
                    print("floor at", pos, size)
                newcuboid (pos, size, 'floor', r)

#
#  generateLimits - output the pen and doom map limits.
#

def generateLimits (o):
    o.write ('    "minx_pen" "' + str (minx) + '"\n')
    o.write ('    "miny_pen" "' + str (miny) + '"\n')
    o.write ('    "maxx_pen" "' + str (maxx) + '"\n')
    o.write ('    "maxy_pen" "' + str (maxy) + '"\n')

    pen_xyz = toIntList ([minx, miny, 0])
    pen_xyz = subVec (pen_xyz, [minx, miny, 0])
    v = midReposition (pen_xyz)
    o.write ('    "minx_doom" "' + str (v[0]) + '"\n')
    o.write ('    "miny_doom" "' + str (v[1]) + '"\n')

    pen_xyz = toIntList ([maxx, maxy, 0])
    pen_xyz = subVec (pen_xyz, [minx, miny, 0])
    v = midReposition (pen_xyz)
    o.write ('    "maxx_doom" "' + str (v[0]) + '"\n')
    o.write ('    "maxy_doom" "' + str (v[1]) + '"\n')
    return o


def generateEntities (o):
    bcount = 0
    o.write ('// entity 0   (contains all room walls, floors, ceilings, lightblocks)\n')
    o.write ('{\n')
    # first entity must have these attributes set
    o.write ('    "classname" "worldspawn"\n')
    o.write ('    "spawnflags" "1"\n')
    o.write ('    "penmap" "' + args.inputfile + '"\n')
    findOffsets ()  # sets minx, miny, minz, maxx, maxy, maxz
    initRoomFloor ()
    o = generateLimits (o)
    vprintf ("room: ")
    for roomNo in list(rooms.keys ()):
        el = roomToEntities (roomNo)
        vprintf ("[%s]", roomNo)
        p = findMinMax (roomNo)
        o.write ("    // room " + roomNo + "\n")
        if False:
            testFaces (roomNo)
        else:
            pushScope (roomNo)
            if roomCuboids:
                for e in el:
                    generateBricks (roomNo, e)
                generateCeiling (roomNo, e)
                generateFloor (roomNo, e)
                generateLightBlocks (roomNo, el)
                generatePlinths (roomNo)
                generateColumns (roomNo)
            if enableSpiralStairs:
                generateStairs (roomNo)
            else:
                generateSimpleStairs (roomNo)
            popScope ()
    vprintf ("\n")
    vprintf ("brick optimisation...")
    o, bcount = flushBricks (o, bcount)
    vprintf ("done\n")
    o.write ('}\n\n')
    return o, 1, bcount


def writeMovableBrick (o, size, material, transform):
    # [length, width, height]
    moveable = cuboid ([0, 0, 0], size, material, transform, None, None)
    o = brick (o, moveable.pos, moveable.size, material, transform)
    return o
    #
    #########################################################################
    #
    if equVec (size, [0.25, 0.5, 0.5]):
        o.write ("\n             ( -1 0 0 84 ) " + transform + " " + material + " 0 0 0")
        o.write ("\n             ( 0 -1 0 72 ) " + transform + " " + material + " 0 0 0")
        o.write ("\n             ( 0 1 0 -96 ) " + transform + " " + material + " 0 0 0")
        o.write ("\n             ( 1 0 0 -96 ) " + transform + " " + material + " 0 0 0")
        o.write ("\n             ( 0 0 -1 0 ) " + transform + " " + material + " 0 0 0")
        o.write ("\n             ( 0 0 1 -24 ) " + transform + " " + material + " 0 0 0")
        o.write ("\n")
    else:
        print ("cannot find brick", size)
    return o


def generateMovable (block, o, e, bcount):
    o.write ("// entity " + str (e) + "\n")
    o.write ("{\n")
    o.write ('  "classname" "moveable_base_brick"\n')
    o.write ('  "name" "moveable_base_brick_' + str (bcount) + '"\n')
    o.write ('  "model" "moveable_base_brick_' + str (bcount) + '"\n')
    x, y, z = calcBrickOrigin (block)
    o.write ('  "origin" "' + str (x) + " " + str (y) + " " + str (z) + '"\n')
    o.write ('  "clipshrink" "1"\n')
    o.write ('    {\n')
    o.write ('         brushDef3\n')
    o.write ('         {\n')
    o = writeMovableBrick (o, block.size, block.material, block.transform)
    o.write ('         }\n')
    o.write ('    }\n')
    o.write ("}\n")
    e += 1
    bcount += 1
    return o, e, bcount


def generateSecretDoors (o, e, bcount):
    bcount = 0
    for k in list (cuboids.keys ()):
        brick = cuboids[k]
        if not brick.fixed:
            o, e, bcount = generateMovable (brick, o, e, bcount)
    return o, e, bcount


#
#  pen2MidPos - pre-condition:  a list of pen coordinates.
#               post-condition:  returns doom3 coordinates
#                                in the middle of the pen coordinate.
#

def pen2MidPos (pos):
    v = []
    for p in translatePos (pos):
        if args.debug:
            print(p)
        v += vecInches2 ([[int (p), halfUnit]])
    return v


#
#  pen2Pos - pre-condition:  pos a coord in pen coordinates.
#            post-condition:  coord in doom3 units.
#

def pen2Pos (pos):
    return vecInches (translatePos (pos))


#
#  translatePos - pre-condition:   pos is a list of numbers (3D pen coordinates).
#                 post-condition:  returns pos - minvec.
#

def translatePos (pos):
    if args.debug:
        print("translatePos called for", pos, minvec, "=", end=' ')
    pos = subVec (pos, minvec)
    pos = [pos[0], pos[1], -pos[2]]
    return pos


#
#  translatePoints - pre-condition:   points is a list of (3D pen coordinates).
#                    post-condition:  returns the list after they have been
#                                     translated.
#

def translatePoints (points):
    global minvec
    result = []
    for p in points:
        result += [subVec (p, minvec)]
    return result


def midReposition (pos):
    v = []
    for p in pos[:-1]:
        # v += vecInches2 ([[int (p), halfUnit]])
        p = vecInches2 ([[int (p), -float (halfUnit)]])
        v += p
    if args.debug:
        print(pos[-1])
    v += [toInches (pos[-1])]
    return v


def getPlinthHeight (r, x, y):
    for plinths in rooms[r].plinths:
        if (plinths[0] == x) and (plinths[1] == y):
            return float (plinths[2]) / inchesPerUnit
    return 0


def generatePlayer (o, player_entity):
    for r in list(rooms.keys()):
        if rooms[r].worldspawn != []:
            o.write ("// entity " + str (player_entity) + '\n')
            o.write ("{\n")
            if args.gametype == "single":
                o.write ('    "classname" "info_player_start"\n')
                o.write ('    "name" "info_player_start_%d"\n' % (player_entity))
            else:
                o.write ('    "classname" "info_player_deathmatch"\n')
                o.write ('    "name" "info_player_deathmatch_%d"\n' % (player_entity))
            o.write ('    "origin" "')
            xy = rooms[r].worldspawn[0]
            xyz = toIntList (xy) + [-invSpawnHeight]
            xyz = subVec (xyz, [minx, miny, getFloorLevel (r) + getPlinthHeight (r, xy[0], xy[1])])
            v = midReposition (xyz)
            o.write ('%f %f %f"\n' % (v[0], v[1], v[2]))
            o.write ('    "angle" "180"\n')
            o.write ("}\n")
            player_entity += 1
    return o, player_entity


def generateLights (o, e):
    n = 1
    for p, l in lightPoints:
        o.write ("// entity " + str (e) + '\n')
        o.write ("{\n")
        o.write ('    "classname" "light"\n')
        o.write ('    "name" "light_' + str (n) + '"\n')
        o.write ('    "origin" "')
        l.writeLightSource (o, p)
        o.write ('    "noshadows" "0"\n')
        o.write ('    "nospecular" "0"\n')
        o.write ('    "nodiffuse" "0"\n')
        if l.getOn () == "FLOOR":
            o.write ('    "falloff" "0.5"\n')
            o.write ('    "texture" "lights/round_flicker"\n')
            o.write ('    "_color" "')
            l.write (o)
            o.write ('"\n')
            o.write ('    "light_radius" "36 36 36"\n')
        else:
            o.write ('    "falloff" "0.0"\n')
            o.write ('    "texture" "lights/round_flicker"\n')
            o.write ('    "_color" "')
            l.write (o)
            o.write ('"\n')
            o.write ('    "light_radius" "225 225 225"\n')
        o.write ("}\n")
        n += 1
        e += 1
    return o, e


def onLine (line, pos):
    if isVertical (line):
        return line[0][0] == pos[0]
    if isHorizontal (line):
        return line[0][1] == pos[1]
    return False


def nextTo (w, p):
    if args.debug:
        print(p)
    p = [int (p[0]), int (p[1])]
    if w[-2] == 'wall':
        line = [[int (w[0][0]), int (w[0][1])], [int (w[1][0]), int (w[1][1])]]
        # print "line =", line,
        if w[-1] == 'left':
            p = addVec (p, [-1, 0])
            # print "p =", p
            return onLine (line, p)
        if w[-1] == 'right':
            p = addVec (p, [1, 0])
            # print "p =", p
            return onLine (line, p)
        if w[-1] == 'top':
            p = addVec (p, [0, 1])
            # print "p =", p
            return onLine (line, p)
        if w[-1] == 'bottom':
            p = addVec (p, [0, -1])
            # print "p =", p
            return onLine (line, p)
    return False


lightOffset = {'left':[1.0, 0], 'right':[0, 0], 'top':[0, 0], 'bottom':[0, 1.0]}


#
#  calcLightOrigin - return the origin for the light source which has a light stand (bricks)
#                    at pos, and, size.
#

def calcLightOrigin (pos, size):
    return addVec (pos, [float (size[0])/2.0, float (size[1])/2.0, 0.0])


#
#  newlight - adds an element into the lightPoints list describing the light source
#             which needs to be added into the map.
#

def newlight (pos, size, desc):
    global lightPoints

    lightPoints += [[calcLightOrigin (pos, size), desc]]
    if args.debug:
        print("new light at", lightPoints[-1], lightPoints[-1][-1].getOn ())


pillarOffset = {'left':[0, 0, 0], 'right':[1.0-lightBlock, 0, 0],
                'top':[0, 1.0-lightBlock, 0], 'bottom':[0, 0, 0],
                'mid':[0.5-lightBlock/2.0, 0.5-lightBlock/2.0, 0]}


#
#  generateLightPillar - places a light pillar in room_no.
#

def generateLightPillar (room_no, light_element, walls):
    light_stand_material = 'plinth'
    light_pos = light_element[0]
    light_obj = light_element[1]
    for wall in walls:
        if nextTo (wall, light_pos):
            if args.debug:
                print ("light at", light_pos, "is next to wall", wall, "in room", room_no)
            # place pillar next to the wall using the offset above
            p0 = [float (light_pos[0]), float (light_pos[1]), getFloorLevel (room_no)]
            size = [lightBlock, lightBlock, lightBlockHeight]
            # print "light is touching a wall", wall
            pos = addVec (p0, pillarOffset[wall[-1]])
            newcuboid (pos, size, light_stand_material, room_no)
            pos = [float (light_pos[0]), float (light_pos[1]), lightHeight]
            pos = addVec (pos, pillarOffset[wall[-1]])
            size = [lightBlock, lightBlock, 0]
            newlight (pos, size, light_obj)
            if args.debug:
                print("pos =", pos, "p0 =", p0, "light =", lightPoints[-1])
            return
    if args.debug:
        print ("light is not touching a wall, placing it in the middle of the square")
    pos = [int (light_pos[0]), int (light_pos[1]), getFloorLevel (room_no)]
    pos = addVec (pos, pillarOffset["mid"])
    size = [lightBlock, lightBlock, lightBlockHeight]
    newcuboid (pos, size, light_stand_material, room_no)
    pos = [int (light_pos[0]), int (light_pos[1]), lightHeight]
    pos = addVec (pos, pillarOffset["mid"])
    size = [lightBlock, lightBlock, 0]
    newlight (pos, size, light_obj)


#
#  generateFloorLight - generate a light on the floor.
#

def generateFloorLight (r, l, walls):
    if args.debug:
        print("floor light seen", end=' ')
    lp = l[0]
    li = l[1]
    for w in walls:
        if nextTo (w, l[0]):
            if args.debug:
                print("light at", l, "is next to wall", w, "in room", r)
            # place light next to the wall using the offset above
            p0 = addVec ([float (lp[0]), float (lp[1])], pillarOffset[w[-1]])
            size = [lightBlock, lightBlock, 0]
            # print "light is touching a wall", l
            pos = [p0[0], p0[1], lightFloorHeight]
            if args.debug:
                print(pos, size)
            newlight (pos, size, li)
            return
    # print "light is not touching a wall", l
    pos = [int (lp[0]), int (lp[1]), lightFloorHeight]
    size = [lightBlock, lightBlock, 0]
    if args.debug:
        print(pos, size)
    newlight (pos, size, li)


#
#  generateCeilingLight - generate a light on the ceiling.
#

def generateCeilingLight (r, l, walls):
    lp = l[0]
    li = l[1]
    for w in walls:
        if nextTo (w, l[0]):
            if args.debug:
                print("light at", l, "is next to wall", w, "in room", r)
            # place light next to the wall using the offset above
            p0 = addVec ([float (lp[0]), float (lp[1])], pillarOffset[w[-1]])
            size = [lightBlock, lightBlock, lightCeilingHeight]
            # print "light is touching a wall", l
            pos = [p0[0], p0[1], 0]
            newlight (pos, size, li)
            return
    # print "light is not touching a wall", l
    pos = [int (l[0]), int (l[1]), 0]
    size = [lightBlock, lightBlock, lightCeilingHeight]
    newlight (pos, size, li)


def generateLightBlocks (r, walls):
    for l in rooms[r].lights:
        if l[1].getOn () == "MID":
            if args.pillarlights:
                generateLightPillar (r, l, walls)
        elif l[1].getOn () == "FLOOR":
            if args.floorlights:
                generateFloorLight (r, l, walls)
        elif l[1].getOn () == "CEIL":
            if args.ceilinglights:
                generateCeilingLight (r, l, walls)
        else:
            error ("unrecognised light position " + l[1].getOn ())


def generatePlinths (r):
    for p in rooms[r].plinths:
        plinthHeight = p[2]
        if plinthHeight > plinthBase + plinthTop + plinthMid * 2:
            height = 0
            #                         [-xy,  +z]  offsets for each component of the plinth
            for xyoffset, zoffset in [[0, plinthBase],
                                      [plinthReduction, plinthMid],
                                      [plinthReduction2, plinthHeight - plinthBase + plinthTop + plinthMid * 2],
                                      [plinthReduction, plinthMid],
                                      [0, plinthTop]]:
                pos = [int (p[0]), int (p[1]), getFloorLevel (r)]
                # pos = addVec (pos, [1, 2, 0])
                # pos = addVec (pos, [minx, miny, 0])
                pos = addVec (pos, [xyoffset / inchesPerUnit, xyoffset / inchesPerUnit, height / inchesPerUnit])
                size = [1, 1, zoffset / inchesPerUnit]
                size = subVec (size, [xyoffset * 2 / inchesPerUnit, xyoffset * 2 / inchesPerUnit, 0])
                newcuboid (pos, size, 'plinth', r)
                height += zoffset
        else:
            pos = [int (p[0]), int (p[1]), getFloorLevel (r)]
            size = [1, 1, float (p[2]) / inchesPerUnit]
            print (pos, size)
            newcuboid (pos, size, 'plinth', r)


def generateColumnBase (r, x, y):
    size = vec (2.0 * 1.4142, 1.0, 1.0)
    origin_offset = vec (1.4142, 0.5, 0)
    pos = vec (int (x), int (y), getFloorLevel (r))
    for segment in range (4):
        moveAndTwist = mat (4).translate (-origin_offset).rotate_z (45.0 * segment)
        baseblock = poly ().unit_cube ().scale (size).mult (moveAndTwist)
        baseblock.sanity_check ()
        baseblock.translate (pos)
        baseblock.sort_vertices ()
        print ("after sort", baseblock)
        baseblock.sanity_check ()
        print ("after sort", baseblock)
        addpolyobj (baseblock.get_vertices (),
                    baseblock.get_faces (),
                    'plinth', r, 'column base')


#
#
#

def generateColumn (r, x, y):
    generateColumnBase (r, x, y)



#
#  generateColumns - for each column generate a pillar.
#

def generateColumns (r):
    for p in rooms[r].columns:
        generateColumn (r, int (p[0]), int (p[1]))


def dumpSimpleVertices (r, bot, size):
    vertices = []
    vertices += [vec (bot[0], bot[1], bot[2])]  # 0
    vertices += [vec (bot[0], bot[1], bot[2] + size[2])]  # 1
    vertices += [vec (bot[0]        , bot[1] + size[1], bot[2])]  # 2
    vertices += [vec (bot[0]        , bot[1] + size[1], bot[2] + size[2])]  # 3
    vertices += [vec (bot[0]+size[0], bot[1]          , bot[2])] # 4
    vertices += [vec (bot[0]+size[0], bot[1]          , bot[2] + size[2])]  # 5
    vertices += [vec (bot[0]+size[0], bot[1] + size[1], bot[2])]  # 6
    vertices += [vec (bot[0]+size[0], bot[1] + size[1], bot[2] + size[2])]  # 7
    for i, vert in enumerate (vertices):
        print (i, vert)


#
#  generateSimpleStairs - for each staircase generate a stair.
#

def generateSimpleStairs (r):
    for stair in rooms[r].stairs:
        startHeight = getFloorLevel (r)
        for s in range (12):
            bot_pos = [int (stair.x) + startHeight,
                       int (stair.y),
                       startHeight]
            stair_end = [int (stair.x)+ startHeight + 1,
                         int (stair.y)+1,
                         startHeight + floorStep]
            size = subVec (stair_end, bot_pos)
            newcuboid (bot_pos, size, 'plinth', r)
            startHeight += floorStep
            dumpSimpleVertices (r, bot_pos, size)


def radian (degree):
    return Decimal (degree) * Decimal (math.pi) / Decimal (180.0)


#
#  generateStairVert - return a list of vertices representing the stair
#                      and wall positions.
#
#                               x0                x1                    x2               x3
#                      (0,0)    (stairWall, 0)    (x0 + stairWall, 0)   (x1 + 2.0)       (x2 + stairWall)
#
#                      |        |                 |                     |                |
#                      +--------+-----------------+---------------------+----------------+
#                        Gap      Inner stairwall    Stair step           Outer stairwall
#
#                      the above values occur at angle 0 degrees.
#                      The returned results are rotated and returned.
#

def generateStairVert (angle):
    x0 = Decimal (stairWall)
    x1 = Decimal (x0 + Decimal (stairWall))
    x2 = Decimal (x1 + Decimal (2.0))
    x3 = Decimal (x2 + Decimal (stairWall))
    x4 = Decimal (x1 + Decimal (stairLight))   # x4 is the left position of the stair light
    x5 = Decimal (x3 - Decimal (stairLight))   # x5 is the right position of the stair light
    theta = radian (Decimal (angle))
    print (x0, x1, x2, x3, x4, x5)
    return [vec (Decimal (math.cos (theta)) * x0, Decimal (math.sin (theta)) * x0, 0),
            vec (Decimal (math.cos (theta)) * x1, Decimal (math.sin (theta)) * x1, 0),
            vec (Decimal (math.cos (theta)) * x2, Decimal (math.sin (theta)) * x2, 0),
            vec (Decimal (math.cos (theta)) * x3, Decimal (math.sin (theta)) * x3, 0),
            vec (Decimal (math.cos (theta)) * x4, Decimal (math.sin (theta)) * x4, 0),
            vec (Decimal (math.cos (theta)) * x5, Decimal (math.sin (theta)) * x5, 0)]


#
#  generateStairs - generate a spiral staircase.
#                   It calculates
#

def generateStairs (r):
    for stair in rooms[r].stairs:
        startHeight = getFloorLevel (r) - 2
        prev_stair_vert = generateStairVert (0)
        z_step = vec (0, 0, floorStep)
        z_wall_right = vec (0, 0, 1.0)
        for s in range (1, 25):
            pos = vec (stair.x,
                       stair.y,
                       startHeight)
            #
            #  left hand wall
            #
            z_wall_left = vec (0, 0, 7.0 - s * floorStep)
            cur_stair_vert = generateStairVert (-stepAngleClockwise * s)
            a = cur_stair_vert[0]
            b = cur_stair_vert[1]
            c = prev_stair_vert[1]
            d = prev_stair_vert[0]
            e = prev_stair_vert[1] + z_wall_left
            f = prev_stair_vert[0] + z_wall_left
            g = cur_stair_vert[0] + z_wall_left
            h = cur_stair_vert[1] + z_wall_left
            stepblock = poly ().unit_cube ().set_vertices ({'a': a,
                                                            'b': b,
                                                            'c': c,
                                                            'd': d,
                                                            'e': e,
                                                            'f': f,
                                                            'g': g,
                                                            'h': h})
            stepblock = stepblock.translate (pos)
            stepblock.sanity_check ()
            print ("before sort", stepblock)
            stepblock.sort_vertices ()
            print ("after sort", stepblock)
            stepblock.sanity_check ()
            print ("after sort", stepblock)
            addpolyobj (stepblock.get_vertices (),
                        stepblock.get_faces (),
                        'wall', r, 'stairs')
            #
            #  right hand wall
            #
            z_wall_left = vec (0, 0, 7.0 - s * floorStep)
            cur_stair_vert = generateStairVert (-stepAngleClockwise * s)
            a = cur_stair_vert[2]
            b = cur_stair_vert[3]
            c = prev_stair_vert[3]
            d = prev_stair_vert[2]
            e = prev_stair_vert[3] + z_wall_left
            f = prev_stair_vert[2] + z_wall_left
            g = cur_stair_vert[2] + z_wall_left
            h = cur_stair_vert[3] + z_wall_left
            stepblock = poly ().unit_cube ().set_vertices ({'a': a,
                                                            'b': b,
                                                            'c': c,
                                                            'd': d,
                                                            'e': e,
                                                            'f': f,
                                                            'g': g,
                                                            'h': h})
            stepblock = stepblock.translate (pos)
            stepblock.sanity_check ()
            print ("before sort", stepblock)
            stepblock.sort_vertices ()
            print ("after sort", stepblock)
            stepblock.sanity_check ()
            print ("after sort", stepblock)
            addpolyobj (stepblock.get_vertices (),
                        stepblock.get_faces (),
                        'wall', r, 'stairs')

            #
            #  the step
            #
            cur_stair_vert = generateStairVert (-stepAngleClockwise * s)
            a = cur_stair_vert[1]
            b = cur_stair_vert[2]
            c = prev_stair_vert[2]
            d = prev_stair_vert[1]
            e = prev_stair_vert[2] + z_step
            f = prev_stair_vert[1] + z_step
            g = cur_stair_vert[1] + z_step
            h = cur_stair_vert[2] + z_step
            light_stair_vert = generateStairVert (-stepAngleClockwise * s -stepAngleClockwise/2.0)
            left = light_stair_vert[4]
            right = light_stair_vert[5]
            stepblock = poly ().unit_cube ().set_vertices ({'a': a,
                                                            'b': b,
                                                            'c': c,
                                                            'd': d,
                                                            'e': e,
                                                            'f': f,
                                                            'g': g,
                                                            'h': h})
            stepblock = stepblock.translate (pos)
            stepblock.sanity_check ()
            print ("before sort", stepblock)
            stepblock.sort_vertices ()
            print ("after sort", stepblock)
            stepblock.sanity_check ()
            print ("after sort", stepblock)
            addpolyobj (stepblock.get_vertices (),
                        stepblock.get_faces (),
                        'wall', r, 'stairs')

            if False:
                pos = vec (stair.x,
                           stair.y,
                           0)
                #
                #  over step light
                #
                left = left + pos + z_step + vec (0, 0, lightFloorHeight + startHeight)
                right = right + pos + z_step + vec (0, 0, startHeight + lightFloorHeight)
                lx, ly, lz = left.to_list ()
                rx, ry, rz = right.to_list ()
                if s in [0]:
                    coke_can (r, float (lx), float (ly), float (lz))
                # coke_can (r, float (rx), float (ry), float (rz))
                # candleStair (r, float (rx), float (ry), float (rz))
                #
                #  under step light
                #
                left = left - vec (0, 0, floorStep + lightFloorHeight)
                right = right - vec (0, 0, floorStep + lightFloorHeight)
                lx, ly, lz = left.to_list ()
                rx, ry, rz = right.to_list ()
                # candleStair (r, float (lx), float (ly), float (lz))
                # candleStair (r, float (rx), float (ry), float (rz))
            #
            #  move onto the next step
            #
            prev_stair_vert = cur_stair_vert
            startHeight += floorStep


def generatePythonMonsters (o, e):
    n = 1
    for r in list (rooms.keys ()):
        for monster, xy in rooms[r].pythonMonsters:
            o.write ("// entity " + str (e) + '\n')
            o.write ("{\n")
            o.write ('    "classname" "' + monster + '"\n')
            o.write ('    "name" "' + monster + '_' + str (n) + '"\n')
            o.write ('    "anim" "idle"\n')
            o.write ('    "origin" "')
            xyz = toIntList (xy) + [-invSpawnHeight]
            xyz = subVec (xyz, [minx, miny, getFloorLevel (r) + getPlinthHeight (r, xy[0], xy[1])])
            v = midReposition (xyz)
            o.write ('%f %f %f"\n' % (v[0], v[1], v[2]))
            o.write ('    "ambush" "1"\n')
            o.write ("}\n")
            n += 1
            e += 1
    return o, e


def generateMonsters (o, e):
    n = 1
    for r in list(rooms.keys()):
        for monster, xy in rooms[r].monsters:
            o.write ("// entity " + str (e) + '\n')
            o.write ("{\n")
            o.write ('    "classname" "' + monster + '"\n')
            o.write ('    "name" "' + monster + '_' + str (n) + '"\n')
            o.write ('    "anim" "idle"\n')
            o.write ('    "origin" "')
            xyz = toIntList (xy) + [-invSpawnHeight]
            xyz = subVec (xyz, [minx, miny, getFloorLevel (r) + getPlinthHeight (r, xy[0], xy[1])])
            v = midReposition (xyz)
            o.write ('%f %f %f"\n' % (v[0], v[1], v[2]))
            o.write ('    "ambush" "1"\n')
            o.write ("}\n")
            n += 1
            e += 1
    return o, e


def generateAmmo (o, entno):
    n = 1
    for room in list(rooms.keys()):
        if args.debug:
            print(rooms[room].ammo)
        for ammo_kind, a, xy in rooms[room].ammo:
            o.write ("// entity " + str (entno) + '\n')
            o.write ("{\n")
            o.write ('    "inv_item" "4"\n')
            o.write ('    "classname" "' + ammo_kind + '"\n')
            o.write ('    "name" "' + ammo_kind + '_' + str (n) + '"\n')
            o.write ('    "origin" "')
            xyz = toIntList (xy) + [-invSpawnHeight]
            xyz = subVec (xyz, [minx, miny,
                                getFloorLevel (room) + getPlinthHeight (room, xy[0], xy[1])])
            v = midReposition (xyz)
            o.write ('%f %f %f"\n' % (v[0], v[1], v[2]))
            o.write ("}\n")
            n += 1
            entno += 1
    return o, entno


def generateSounds (o, e):
    n = 1
    for r in list(rooms.keys()):
        if args.debug:
            print(rooms[r].sounds)
        for s, xy in rooms[r].sounds:
            o.write ("// entity " + str (e) + '\n')
            o.write ("{\n")
            o.write ('    "classname" "speaker"\n')
            o.write ('    "name" "speaker_%d"\n' % e)
            o.write ('    "origin" "')
            xyz = toIntList (xy) + [-invSpawnHeight]
            xyz = subVec (xyz, [minx, miny, getFloorLevel (r) + getPlinthHeight (r, xy[0], xy[1])])
            v = midReposition (xyz)
            o.write ('%f %f %f"\n' % (v[0], v[1], v[2]))
            o.write ('    "s_shader" "%s"\n' % s.filename)
            o.write ('    "s_mindistance" "%s"\n' % s.mindist)
            o.write ('    "s_maxdistance" "%s"\n' % s.maxdist)
            o.write ('    "s_volume" "%s"\n' % s.volume)
            o.write ('    "s_omni" "0"\n')
            o.write ('    "s_occlusion" "0"\n')
            o.write ('    "soundgroup" ""\n')
            o.write ('    "s_leadthrough" "0.100000"\n')
            o.write ('    "s_plain" "0"\n')
            o.write ('    "wait" "%s"\n' % s.wait)
            o.write ('    "random" "0.000000"\n')
            o.write ('    "s_looping" "1"\n')
            o.write ('    "s_unclamped" "0"\n')
            o.write ('    "s_justVolume" "1"\n')
            o.write ("}\n")
            n += 1
            e += 1
    return o, e


def generateWeapons (o, e):
    n = 1
    for r in list(rooms.keys ()):
        if args.debug:
            print(rooms[r].weapons)
        for weapon_kind, xy in rooms[r].weapons:
            o.write ("// entity " + str (e) + '\n')
            o.write ("{\n")
            o.write ('    "inv_item" "4"\n')
            o.write ('    "classname" "' + weapon_kind + '"\n')
            o.write ('    "name" "' + weapon_kind + '"\n')
            o.write ('    "origin" "')
            xyz = toIntList (xy) + [-invSpawnHeight]
            xyz = subVec (xyz, [minx, miny, getFloorLevel (r) + getPlinthHeight (r, xy[0], xy[1])])
            v = midReposition (xyz)
            o.write ('%f %f %f"\n' % (v[0], v[1], v[2]))
            o.write ("}\n")
            n += 1
            e += 1
    return o, e


def generateLabels (o, e):
    n = 1
    for r in list(rooms.keys ()):
        if args.debug:
            print (rooms[r].labels)
        for label_desc, xy in rooms[r].labels:
            o.write ("// entity " + str (e) + '\n')
            o.write ("{\n")
            o.write ('    "classname" "item_default"\n')
            o.write ('    "name" "label_' + str (n) + '"\n')
            o.write ('    "label" "' + label_desc + '"\n')
            o.write ('    "origin" "')
            xyz = toIntList (xy) + [-invSpawnHeight]
            xyz = subVec (xyz, [minx, miny, getFloorLevel (r) + getPlinthHeight (r, xy[0], xy[1])])
            v = midReposition (xyz)
            o.write ('%f %f %f"\n' % (v[0], v[1], v[2]))
            o.write ("}\n")
            n += 1
            e += 1
    return o, e


def generateCokeCans (o, e):
    n = 1
    for roomno in list (rooms.keys ()):
        if args.debug:
            print (rooms[roomno].cokeCans)
        for can in rooms[roomno].cokeCans:
            o.write ("// entity " + str (e) + '\n')
            o.write ("{\n")
            o.write ('    "inv_item" "4"\n')
            o.write ('    "classname" "moveable_cokecan"\n')
            o.write ('    "name" "movable_cokecan_' + str (n) + '"\n')
            o.write ('    "origin" "')
            x = toInches (can.x - minx)
            y = toInches (can.y - miny)
            z = toInches (can.z - getFloorLevel (roomno))
            z += getFloorLevel (roomno)
            o.write ('%d %d %d"\n' % (x, y, z))
            o.write ("}\n")
            n += 1
            e += 1
    return o, e


def assignFloorLevel (f):
    global rooms
    for r in list(rooms.keys()):
        rooms[r].floorLevel = f


def generateMap (o):
    if args.floor:
        calcFloorLevel ()
    else:
        assignFloorLevel (0)
    o.write ("// automatically created from: " + args.inputfile + "\n")
    o       = generateVersion (o)
    o, e, b = generateEntities (o)
    o, e    = generatePlayer (o, e)
    o, e    = generatePythonMonsters (o, e)
    o, e    = generateMonsters (o, e)
    o, e    = generateLights (o, e)
    o, e    = generateAmmo (o, e)
    o, e    = generateSounds (o, e)
    o, e    = generateWeapons (o, e)
    o, e    = generateLabels (o, e)
    o, e, b = generateSecretDoors (o, e, b)
    o, e    = generateCokeCans (o, e)
    if args.statistics:
        print("Total rooms =", len (list (rooms.keys ())))
        print("Total cuboids =", len (list (cuboids.keys ())))
        print("Total cuboids expanded (optimised) =", getexpanded ())
        print("Total entities used =", e, "entities unused =", maxEntities-e)
        print("Total brushes used  =", b)
    return o


#
#  getSpawnRoom - return the room in which the player is spawned.
#

def getSpawnRoom ():
    for r in list(rooms.keys ()):
        if rooms[r].worldspawn != []:
            return r
    return None


#
#  getListOfRooms - return the complete list of rooms.
#

def getListOfRooms ():
    return list(rooms.keys ())


#
#  getNeighbours - return the neighbouring rooms for room, r.
#

def getNeighbours (r):
    n = []
    for d in r.doors:
        n += [d[1]]
    return n


#
#  getVirtualNeighbours - return the neighbouring rooms for room, r.
#                         A virtual neighbour will never have an adjoining secret door.
#

def getVirtualNeighbours (r):
    # print ("getVirtualNeighbours =", r)
    virtList = getVirtualRoom (r)
    # print ("virtual room", virtList)
    n = []
    for i in virtList:
        r = rooms[i]
        for d in r.doors:
            if d[2] != status_secret:
                if (not (d[1] in virtList)) and (not (d[1] in n)):
                    n += [d[1]]
    # print ("virtual neighbours", n)
    return n


#
#  getVirtualRoom - return a list of rooms which are rooms connected by secret doors.
#

def getVirtualRoom (r):
    todo = [r]
    # print ("todo =", todo)
    visited = []
    virtualRoomList = [r]
    while todo != []:
        nextTodo = []
        for r in todo:
            if not (r in visited):
                visited += [r]
                # print ("r =", r)
                for c in todo:
                    for d in rooms[r].doors:
                        if d[2] == status_secret:
                            if not (d[1] in virtualRoomList):
                                virtualRoomList += [d[1]]
                            if not (d[1] in visited):
                                nextTodo += [d[1]]
        todo = nextTodo
    return virtualRoomList


#
#  lowerFloors - starting at room, s, lower all neighbouring floors
#                This is a breadth first algorithm.
#

def lowerFloors (s):
    visited = [s]
    queue = getVirtualNeighbours (s)
    level = -(floorStep * noSteps)
    while queue != []:
        nextLevel = []
        for c in queue:
            roomList = getVirtualRoom (c)
            for i in roomList:
                r = rooms[i]
                if r.floorLevel == None:
                    r.floorLevel = level
                    nextLevel += getVirtualNeighbours (i)
        queue = nextLevel
        level -= (floorStep * noSteps)


#
#  calcFloorLevel - starting at the room with the spawn point
#

def calcFloorLevel ():
    global minFloor, maxFloor
    for s in getVirtualRoom (getSpawnRoom ()):
        rooms[s].floorLevel = 0
    lowerFloors (getSpawnRoom ())
    for r in list (rooms.keys ()):
        if debugFloorLevel:
            print ("room", r, "has floor level", end=' ')
        if rooms[r].floorLevel is None:
            rooms[r].floorLevel = 0
            if debugFloorLevel:
                print ("(0)")
        else:
            if debugFloorLevel:
                print (rooms[r].floorLevel)
        minFloor = min (minFloor, rooms[r].floorLevel)
        maxFloor = max (minFloor, rooms[r].floorLevel)


#
#  checkRegression - regression test if needed.
#

def checkRegression ():
    if regressionRequired:
        setOptimise (True)
        regressiontest ()
    setOptimise (optimise)
    unit_tests ()
    dump_unit_coords ()


def dump_unit_coords ():
    toppos = [1, 1, 1]
    botpos = [0, 0, 0]
    size = subVec (toppos, botpos)
    points = [botpos,
              addVec (botpos, [0, size[1], 0]),
              addVec (botpos, [size[0], size[1], 0]),
              addVec (botpos, [size[0], 0, 0]),
              toppos,
              subVec (toppos, [0, size[1], 0]),
              subVec (toppos, [size[0], size[1], 0]),
              subVec (toppos, [size[0], 0, 0])]
    print ("unit coords")
    for p in points:
        print (p)


#
#  main - handle the input/output file options and call processMap.
#

def main ():
    global words, args
    args = initOptions ()
    checkRegression ()
    if args.inputfile == '-':
        # input file not set so use stdin
        inf = sys.stdin
    else:
        inf = open (args.inputfile, 'r')
    if args.outputfile == '-':
        # output file not set so use stdout
        opf = sys.stdout
    else:
        opf = open (args.outputfile, 'w')
    words = lexicalPen (inf)
    if parsePen ():
        if args.txt:
            opf = generateTxt (opf)
        else:
            opf = generateMap (opf)
        opf.flush ()


main ()
