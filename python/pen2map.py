#!/usr/bin/env python3

# Copyright (C) 2017-2021
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
from chvec import *
from chcuboid import *
import math, random


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

defaultTextureConfig := ( "CEILING" | "FLOOR" | "WALL" | "PLINTH" ) string =:

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

inputFile = None
defines = {}
verbose = False
debugging = False
debugFloorLevel = False
comments = False
statistics = False
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
status_open, status_closed, status_secret = list(range(3))
curRoom = None
curRoomNo = None
curPos = None
direction = ["left", "top", "right", "bottom"]
doorStatus = ["open", "closed", "secret"]
maxEntities = 4096    # doom3 limitation
singlePlayer, deathMatch = list(range(2))
gameType = singlePlayer
genSteps = False
maxd3Units = 5000
minx, miny, minz, maxz = None, None, None, None
lightPoints = []
optimise = False
regressionRequired = False
curCol = []
defaultOn = "MID"
curOn = defaultOn
defaultColour = [150, 150, 150]
autoBeams = False
enableVisportals = False
minFloor, maxFloor = 0, 0
enablePitched = False
enableCeilingLights = False
enableFloorLights = True
enablePillarLights = True
enableCandleLights = True
defaults = { "portal":"textures/editor/visportal",
             "open":"textures/editor/visportal",
             "closed":"textures/hell/wood1",
             "secret":"secret",
             "wall":"textures/hell/cbrick2",
             "floor":"textures/hell/qfloor",
             "ceiling":"textures/hell/wood1",
             "brick" : "textures/caves/sbricks2",
             "open_transform"   :"( ( 0.0078125 0 0 ) ( 0 0.0078125 1.5 ) )",
             # portal transform is a no-op but it allows code reuse.
             "portal_transform" :"( ( 0.0078125 0 0 ) ( 0 0.0078125 1.5 ) )",
             "wall_transform"   :"( ( 0.0078125 0 0.5 ) ( 0 -0.0078125 -1 ) )",
             ##### "wall_transform"   :"( ( 0.0156250019 0 1.0000002384 ) ( 0 0.015625 6.25 ) )",
             "floor_transform"  :"( ( 0.03 0 0 ) ( 0 0.03 0 ) )",
             "plinth_transform" :"( ( 0.03 0 0 ) ( 0 0.03 0 ) )",
             "ceiling_transform":"( ( 0.0078125 0 0 ) ( 0 0.0078125 0 ) )",
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
lightFloorHeight   = 0.125     # 6 inches
lightCeilingHeight = minCeilingHeight - 1.5
floorStep          = 0.25      # 1 foot
noSteps            = 4         # how many steps per unit
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


cuboidno = 1          #  total number of cuboids used.
cuboids = {}
roofno = 1
roofBricks = {}


#
#  verify_polygon_points - runs a conistency check to ensure all points are unique.
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

def addroofbrick (polygon_points, faces, material, r):
    global roofBricks, roofno

    roofBricks[roofno] = roofbrick (polygon_points, faces,
                                    lookupMaterial (r, material),
                                    lookupTransform (r, material))
    roofno += 1


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
    if debugging:
        print ("examine cuboid", pos, size, end=' ')
    for k in list(cuboids.keys ()):
        b = cuboids[k]
        if (b.material != material) or (b.transform != transform):
            if b.interpenetration (pos, size):
                print ("brick at", pos, size, "intersects with", b.pos, b.size, b.cuboidno)
                error ("brick is being overwritten   (consider giving the room number for more detail)  the two cubiods have material " + b.material + " and " + material)
            # differing material cannot be merged.
            if debugging:
                print ("differing material")
            return False
        if b.combined (pos, size, material, transform, fixed):
            if debugging:
                print ("combined!")
            return True
    if debugging:
        print ("no join")
    return False


#
#  alreadyExists - returns True if the cuboid already exists.
#

def alreadyExists (pos, size, material, transform):
    if debugging:
        print ("checking", material)
    for k in list (cuboids.keys ()):
        b = cuboids[k]
        if (b.material == material) and (b.transform == transform):
            if b.subset (pos, size):
                if debugging:
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


#
#  lookupEntry - returns the entry for, name, in the stacked scope stack.
#

def lookupEntry (name):
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
    print(str(format) % args, end=' ')


#
#  error - issues an error message and exits.
#

def error (format, *args):
    print(str (format) % args, end=' ')
    sys.exit (1)


#
#  warning - issues a warning message and exits.
#

def warning (format, *args):
    s = str (format) % args
    sys.stderr.write (s)
    sys.exit (1)


#
#  debugf - issues prints if debugging is set
#

def debugf (format, *args):
    global debugging
    if debugging:
        print(str (format) % args, end=' ')


#
#  vprintf - verbose printf
#

def vprintf (format, *args):
    if verbose:
        print(str(format) % args, end=' ')
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


def usage (code):
    print("Usage: pen2map [-c filename.ss] [-defhmtvV] [-o outputfile] inputfile")
    print("  -b                introduce beams and ceiling candle lights")
    print("  -c filename.ss    use filename.ss as the defaults for the map file")
    print("  -d                debugging")
    print("  -e                provide comments in the map file")
    print("  -f                introduce steps between rooms")
    print("  -g type           game type.  The type must be 'single' or 'deathmatch'")
    print("  -h                help")
    print("  -m                create a doom3 map file from the pen file")
    print("  -p                generate visportals")
    print("  -q                a pitched ceiling for four walled rooms")
    print("  -s                generate statistics about the map file")
    print("  -t                create a txt file from the pen file")
    print("  -C                disable candle lights on beams")
    print("  -P                disable lights on pillars")
    print("  -F                disable lights on the floor")
    print("  -O                optimize cuboid generation")
    print("  -V                generate verbose information")
    print("  -v                print the version")
    print("  -o outputfile     place output into outputfile")
    sys.exit (code)


#
#  handleOptions -
#

def handleOptions ():
    global debugging, verbose, outputName, toTxt, toMap, ssName
    global comments, statistics, gameType, genSteps, optimise
    global regressionRequired, autoBeams, enableVisportals, enablePitched
    global enableFloorLights, enablePillarLights, enableCandleLights

    outputName = None
    try:
        optlist, l = getopt.getopt(sys.argv[1:], ':bc:defg:hmo:pqrstvVOCFP')
        for opt in optlist:
            if opt[0] == '-b':
                autoBeams = True
            elif opt[0] == '-c':
                ssName = opt[1]
            elif opt[0] == '-d':
                debugging = True
            elif opt[0] == '-e':
                comments = True
            elif opt[0] == '-f':
                genSteps = True
            elif opt[0] == '-g':
                if opt[1] == 'single':
                    gameType = singlePlayer
                elif opt[1] == 'deathmatch':
                    gameType = deathMatch
                else:
                    usage (1)
            elif opt[0] == '-h':
                usage (0)
            elif opt[0] == '-p':
                enableVisportals = True
            elif opt[0] == '-q':
                enablePitched = True
            elif opt[0] == '-o':
                outputName = opt[1]
            elif opt[0] == '-v':
                printf ("pen2map version %s\n", versionNumber)
                sys.exit (0)
            elif opt[0] == '-t':
                toTxt = True
            elif opt[0] == '-s':
                statistics = True
            elif opt[0] == '-r':
                regressionRequired = True
            elif opt[0] == '-m':
                toMap = True
            elif opt[0] == '-C':
                enableCandleLights = False
            elif opt[0] == '-P':
                enablePillarLights = False
            elif opt[0] == '-F':
                enableFloorLights = False
            elif opt[0] == '-V':
                verbose = True
            elif opt[0] == '-O':
                optimise = True
        if toTxt and toMap:
            print ("you need to choose either a text file or map file but not both")
            usage (1)
        readDefaults (ssName)
        if l != []:
            return (l[0], outputName)
        print ("you need to supply an input file or use - for stdin")
        usage (1)

    except getopt.GetoptError:
       usage (1)
    return (None, outputName)


def errorLine (text):
    global inputFile, currentLineNo
    full = "%s:%d:%s\n" % (inputFile, currentLineNo, text)
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
    if debugging:
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
    global curRoom, curInteger, curRoomNo, verbose
    if expecting (['ROOM']):
        expect ("ROOM")
        if integer ():
            curRoomNo = curInteger
            curRoom = newRoom (curRoomNo)
            if debugging:
                print("roomDesc", curRoomNo)
            while expecting (['DOOR', 'WALL', 'TREASURE', 'AMMO', 'WEAPON', 'LIGHT', 'INSIDE', 'MONSTER', 'SPAWN', 'DEFAULT', 'SOUND', 'LABEL', 'PLINTH']):
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
            expect ('END')
            return True
        else:
            errorLine ('expecting an integer after ROOM')
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
    if debugging:
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
    if debugging:
        print("orderWalls, entered")
        for i in w:
            print(i)
    n = []
    i = findLowestLeftVertical (w)
    if debugging:
        print("findLowestLeftVertical =", i)
    n += [sortWall (w[i])]
    e = getHighest (w[i])
    if debugging:
        print("w[i] =", w[i], "e =", e)
    p = [getLowest (w[i])]
    if debugging:
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
        if debugging:
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
        if debugging:
            print("3rd p =", p, "e =", e)
        del w[i]
    if debugging:
        print("orderWalls, exiting with", n)
    if not isVertical (n[0]):
        internalError ('expecting first wall to be vertical')
    return n


def createBoxes (r, w, d):
    if debugging:
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
    if debugging:
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
    if debugging:
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
    if debugging:
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
    if debugging:
        print("lowest left, p =", p)
    for i, w in enumerate (walls):
        if debugging:
            print("direction", d, "position", p, "looking at", w)
        checkOnWall (r, p, w)
        if (d == 0) or (d == 2):
            # on left or right vertical wall
            if movesRight (w, p):
                d = 1  # from left to top wall
                if debugging:
                    print("moves to top because of wall", w)
            elif movesLeft (w, p):
                d = 3  # from left to bottom wall
                if debugging:
                    print("moves to bottom because of wall", w)
        else:
            # must be on either top or bottom wall
            if movesUp (w, p):
                d = 0  # from top/bottom to left vertical wall
                if debugging:
                    print("moves to left because of wall", w)
            elif movesDown (w, p):
                d = 2  # from top/bottom to right vertical wall
                if debugging:
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
        if debugging:
            print("entity list", e)
    if debugging:
        print("entity list is", e)
    return e


def roomToEntities (r):
    w = orderWalls (r, rooms[r].walls)
    if debugging:
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
#  reorder the coordinates to make a lowest, left, back corner
#  b highest, top, right corner
#

def reorderVertices (a, b):
    assert (len (a) == len (b))
    c = []
    d = []
    for i, j in zip (a, b):
        c += [min (i, j)]
        d += [max (i, j)]
    return c, d


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


def isNearZero (r):
    return abs (r) < 0.0001


def verify_point_on_plane (vec, distance, p):
    p = decimalVec (vecInches (p))
    A = vec[0] * p[0]
    B = vec[1] * p[1]
    C = vec[2] * p[2]
    D = distance
    assert (isNearZero (A + B + C + D))

def verify_plane_points (vec, distance, f, polygon_points):
    for i in f:
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
#  flushCuboids - flush all the cuboid bricks which have the same fixed
#                 value.
#

def flushCuboids (o, bcount, fixed):
    for k in list (cuboids.keys ()):
        b = cuboids[k]  # Python v2 and v3 compatible
        if b.fixed == fixed:
            if debugging:
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
    for k in list(roofBricks.keys ()):
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
#  flushBricks - flushes all used fixed cuboids to the output file, o
#

def flushBricks (o, bcount):
    o, bcount = flushCuboids (o, bcount, True)
    o, bcount = flushRoofBricks (o, bcount)
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
    if comments:
        o.write ('             ')
        o.write ("// " + str (e) + '\n')
    if debugging:
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
    if debugging:
        print("vertical steps in room", r, e)
    leftLevel  = rooms[str (getFloor (e[0][0]-1, e[0][1]))].floorLevel
    rightLevel = rooms[str (getFloor (e[0][0]+1, e[0][1]))].floorLevel
    winc = 1.0/float (noSteps)
    # quit ()
    if leftLevel == rightLevel:
        hinc = 0
    else:
        hinc = floorStep
    if debugging:
        print("rightLevel =", rightLevel, "leftLevel =", leftLevel, "winc =", winc, "hinc =", hinc)
    widthOffset = 0
    heightOffset = 0
    for s in range (noSteps):
        pos = [e[0][0]+widthOffset, l, minFloor-1]
        if debugging:
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
    if debugging:
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
#  doOpen - create an open door.
#

def doOpen (r, e):
    global minFloor, maxFloor
    if debugging:
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
            if debugging:
                print("vertical ceiling block at", pos, end, size)
            newcuboid (pos, size, 'wall', r)   # ceiling
            if enableVisportals:
                # visportal doorway
                #
                # (your code goes here)
                #
                # fill in the doorway with visportal block
                # vertical visportal code
                pass
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
            if debugging:
                print("horiz ceiling block at", pos, end, size)
            newcuboid (pos, size, 'wall', r)   # ceiling
            if enableVisportals:
                # visportal doorway
                #
                # (your code goes here)
                #
                # horizontal visportal doorway
                pass


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
    if debugging:
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
            if debugging:
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
            if debugging:
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
    if debugging:
        print("room", r, e, end=' ')
    if brickFunc[e[-1]+e[-2]] == None:
        warning ("do not know how to build " + str (e) + " in room " + r)
    #
    # doorways are known about from both rooms, but we only need to build it once
    #
    if alreadyBuilt (e):
        if debugging:
            print("aready built")
    else:
        brickFunc[e[-1]+e[-2]] (r, e)
    setBuilt (e)


#
#  generateBrushes - each wall is made up from a single entity.
#                    Each entity will have 6 faces for a building block.
#

def generateBrushes (r, e, o, bcount):
    if debugging:
        print("room", r, e, end=' ')
    if entityFunc[e[-1]+e[-2]] == None:
        warning ("do not know how to build brush" + str (e) + "in room " + r)
        return o, bcount
    if alreadyBuilt (e):
        if debugging:
            print("aready built")
        return o, bcount
    if debugging:
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
    if debugging:
        for f in floor:
            print(f)


def candle (r, x, y):
    pos = [x, y, candleHeight]
    size = [0.5, 0.5, 0.0]
    col = scopeColourRoom (r, "CEIL")
    newlight (pos, size, light (col, "CEIL", r))


def beamSupport (r, x, y, h):
    pos = [x, y, h]
    size = [beamSupportSize, beamSupportSize, beamSupportSize]
    newcuboid (pos, size, 'wall', r)


def beamTransim (r, botpos, toppos, translate_top):
    points, faces = generate_roof_points (botpos, toppos, translate_top)
    addroofbrick (points, faces, "ceiling", r)   # facing up 2D when viewed from top


def makeBeamX (r, x, y0, y1):
    h = getFloorLevel (r) + minCeilingHeight - 0.5
    if debugging:
        print("beamX", x, y0, y1, h)
    #
    #  main flat, support beam
    #
    for y in range (y0+1, y1):
        pos = [x, y, h]
        size = [0.5, 1.0, 0.5]
        if debugging:
            print("beamX block", x, y, h)
        newcuboid (pos, size, 'ceiling', r)
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
    if debugging:
        print("beamY", x0, x1, y, h)
    #
    #  main flat, support beam
    #
    for x in range (x0+1, x1):
        pos = [x, y, h]
        size = [1.0, 0.5, 0.5]
        if debugging:
            print("beamY block", x, y, h)
        newcuboid (pos, size, 'ceiling', r)
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


def makeCandleX (r, x, y0, y1):
    if enableCandleLights:
        candle (r, x, y0+1.0)
        candle (r, x, y1-0.5)


def makeCandleY (r, x0, x1, y):
    if enableCandleLights:
        candle (r, x0+1.0, y)
        candle (r, x1-0.5, y)

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
    if debugging:
        print("is", x, y, "on a door")
    for r in list(rooms.keys ()):
        for d in rooms[r].doors:
            coords = d[0]
            if coords[0][0] == coords[1][0]:
                # vertical
                if (x == coords[0][0]) and inBetween (y, coords[0][1], coords[1][1]):
                    if debugging:
                        print("yes")
                    return True
            else:
                # horizontal
                if (y == coords[0][1]) and inBetween (x, coords[0][0], coords[1][0]):
                    if debugging:
                        print("yes")
                    return True
    if debugging:
        print("no")
    return False


#
#  generateBeams - generate beams and light for 4 sided rooms.
#

def generateBeams (r, e):
    if len (rooms[r].walls) == 4:
        if debugging:
            print("room", r, "beams being created")
        p = findMinMax (r)
        w0, w1 = None, None
        if debugging:
            print(r, p)
            print(rooms[r].walls)
        x0, y0 = p[0]
        x1, y1 = p[1]
        if debugging:
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
            if debugging:
                print(w0, w1)
            for x in range (w0[0][0]+1, w0[1][0], 4):
                if (not onDoor (x, y0)) and (not onDoor (x, y1)):
                    makeBeamX (r, x, y0, y1)
            for x in range (w0[0][0]+3, w0[1][0], 4):
                if (not onDoor (x, y0)) and (not onDoor (x, y1)):
                    makeCandleX (r, x, y0, y1)
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
            if debugging:
                print(w0, w1)
            for y in range (w0[0][1]+1, w0[1][1], 4):
                if (not onDoor (x0, y)) and (not onDoor (x1, y)):
                    makeBeamY (r, x0, x1, y)
            for y in range (w0[0][1]+3, w0[1][1], 4):
                if (not onDoor (x0, y)) and (not onDoor (x1, y)):
                    makeCandleY (r, x0, x1, y)


#
#  generateFlatCeiling - generate a simple flat surface (slab) at
#                        rooms[r].floorLevel+minCeilingHeight .. minCeilingHeight
#                        on the Z axis.
#

def generateFlatCeiling (r, e):
    for x in range (1, maxx):
        for y in range (1, maxy):
            if getFloor (x, y) == int (r):
                pos = [x, y, getFloorLevel (r) + minCeilingHeight]
                end = [x+1, y+1, getFloorLevel (r) + minCeilingHeight + 1.0]
                size = subVec (end, pos)
                newcuboid (pos, size, 'ceiling', r)


def apply_translate_top (points, translate_top, z_value):
    if debugging:
        print("z_value =", z_value)
        print("before", points)
    translated = []
    for p in points:
        if p[2] == z_value:
            if debugging:
                print("translating", translate_top)
            translated += [addVec (p, translate_top)]
        else:
            translated += [p]
    if debugging:
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
    points = []
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
    if debugging:
        print("cuboid roof =", points)
    points = apply_translate_top (points, translate_top, botpos[2])
    if debugging:
        print("slanted roof =", points)
    return points, faces


def generatePitchedCeiling (r, e):
    if debugging:
        print("generatePitchedCeiling")
    if len (rooms[r].walls) == 4:
        p = findMinMax (r)
        x0, y0 = p[0]
        x1, y1 = p[1]
        if debugging:
            print("simple room", r, "coords", x0, y0, x1, y1)
        h = getFloorLevel (r) + minCeilingHeight
        if abs (x0-x1) > abs (y0-y1):
            x0, x1 = sortMinMax (x0, x1)
            y0, y1 = sortMinMax (y0, y1)
            if debugging:
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
            if debugging:
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


def generateCeiling (r, e):
    if (len (rooms[r].walls) == 4) and enablePitched:
        generatePitchedCeiling (r, e)
    else:
        generateFlatCeiling (r, e)
    if autoBeams:
        generateBeams (r, e)


def generateFloor (r, e):
    global minFloor, maxFloor
    for x in range (1, maxx):
        for y in range (1, maxy):
            if getFloor (x, y) == int (r):
                pos = [x, y, minFloor-1]
                size = [1, 1, rooms[r].floorLevel-minFloor+1]
                if debugging:
                    print("floor at", pos, size)
                newcuboid (pos, size, 'floor', r)

#
#  generateLimits - output the pen and doom map limits.
#

def generateLimits (o):
    o.write ('    "penminx" "' + str (minx) + '"\n')
    o.write ('    "penminy" "' + str (miny) + '"\n')
    o.write ('    "penmaxx" "' + str (maxx) + '"\n')
    o.write ('    "penmaxy" "' + str (maxy) + '"\n')

    pen_xyz = toIntList ([minx, miny, 0])
    pen_xyz = subVec (pen_xyz, [minx, miny, 0])
    v = midReposition (pen_xyz)
    o.write ('    "doomminx" "' + str (v[0]) + '"\n')
    o.write ('    "doomminy" "' + str (v[1]) + '"\n')

    pen_xyz = toIntList ([maxx, maxy, 0])
    pen_xyz = subVec (pen_xyz, [minx, miny, 0])
    v = midReposition (pen_xyz)
    o.write ('    "doommaxx" "' + str (v[0]) + '"\n')
    o.write ('    "doommaxy" "' + str (v[1]) + '"\n')
    return o


def generateEntities (o):
    bcount = 0
    o.write ('// entity 0   (contains all room walls, floors, ceilings, lightblocks)\n')
    o.write ('{\n')
    # first entity must have these attributes set
    o.write ('    "classname" "worldspawn"\n')
    o.write ('    "spawnflags" "1"\n')
    o.write ('    "penmap" "' + inputFile + '"\n')
    findOffsets ()  # sets minx, miny, minz, maxx, maxy, maxz
    initRoomFloor ()
    o = generateLimits (o)
    vprintf ("room: ")
    for r in list(rooms.keys ()):
        el = roomToEntities (r)
        vprintf ("[%s]", r)
        p = findMinMax (r)
        o.write ("    // room " + r + "\n")
        if False:
            testFaces (r)
        else:
            for e in el:
                generateBricks (r, e)
            generateCeiling (r, e)
            generateFloor (r, e)
            generateLightBlocks (r, el)
            generatePlinths (r)
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
        if debugging:
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
    if debugging:
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
    if debugging:
        print(pos[-1])
    v += [toInches (pos[-1])]
    return v


def getPlinthHeight (r, x, y):
    for plinths in rooms[r].plinths:
        if (plinths[0] == x) and (plinths[1] == y):
            return float (plinths[2]) / inchesPerUnit
    return 0

def generatePlayer (o, e):
    for r in list(rooms.keys()):
        if rooms[r].worldspawn != []:
            o.write ("// entity " + str (e) + '\n')
            o.write ("{\n")
            if gameType == singlePlayer:
                o.write ('    "classname" "info_player_start"\n')
                o.write ('    "name" "info_player_start_1"\n')
            else:
                o.write ('    "classname" "info_player_deathmatch"\n')
                o.write ('    "name" "info_player_deathmatch_1"\n')
            o.write ('    "origin" "')
            xy = rooms[r].worldspawn[0]
            xyz = toIntList (xy) + [-invSpawnHeight]
            xyz = subVec (xyz, [minx, miny, getFloorLevel (r) + getPlinthHeight (r, xy[0], xy[1])])
            v = midReposition (xyz)
            o.write ('%f %f %f"\n' % (v[0], v[1], v[2]))
            o.write ('    "angle" "180"\n')
            o.write ("}\n")
    return o, e+1


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
        o.write ('    "falloff" "0.000000"\n')
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
    if debugging:
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
    if debugging:
        print("new light at", lightPoints[-1], lightPoints[-1][-1].getOn ())


pillarOffset = {'left':[0, 0], 'right':[1.0-lightBlock, 0], 'top':[0, 1.0-lightBlock], 'bottom':[0, 0]}


def generateLightPillar (r, l, el):
    light_stand_material = 'wall'
    lp = l[0]
    li = l[1]
    for w in el:
        if nextTo (w, l[0]):
            if debugging:
                print("light at", l, "is next to wall", w, "in room", r)
            # place pillar next to the wall using the offset above
            # p0 = addVec ([float (lp[0]), float (lp[1])], pillarOffset[w[-1]])
            p0 = [float (lp[0]), float (lp[1]), getFloorLevel (r)]
            size = [lightBlock, lightBlock, lightBlockHeight]
            # print "light is touching a wall", l
            pos = [p0[0], p0[1], getFloorLevel (r)]
            newcuboid (pos, size, light_stand_material, r)
            # size = [lightBlock, lightBlock, lightHeight]
            pos = [float (lp[0]), float (lp[1]), lightHeight]
            size = [lightBlock, lightBlock, 0]
            newlight (pos, size, li)
            if debugging:
                print("pos =", pos, "p0 =", p0, "light =", lightPoints[-1])
            return
    return
    print("light is not touching a wall", l)
    pos = [int (lp[0]), int (lp[1]), getFloorLevel (r)]
    size = [lightBlock, lightBlock, lightBlockHeight]
    newcuboid (pos, size, light_stand_material, r)
    pos = [int (lp[0]), int (lp[1]), lightHeight]
    size = [lightBlock, lightBlock, 0]
    newlight (pos, size, li)


#
#  generateFloorLight - generate a light on the floor.
#

def generateFloorLight (r, l, walls):
    if debugging:
        print("floor light seen", end=' ')
    lp = l[0]
    li = l[1]
    for w in walls:
        if nextTo (w, l[0]):
            if debugging:
                print("light at", l, "is next to wall", w, "in room", r)
            # place light next to the wall using the offset above
            p0 = addVec ([float (lp[0]), float (lp[1])], pillarOffset[w[-1]])
            size = [lightBlock, lightBlock, 0]
            # print "light is touching a wall", l
            pos = [p0[0], p0[1], lightFloorHeight]
            if debugging:
                print(pos, size)
            newlight (pos, size, li)
            return
    # print "light is not touching a wall", l
    pos = [int (lp[0]), int (lp[1]), lightFloorHeight]
    size = [lightBlock, lightBlock, 0]
    if debugging:
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
            if debugging:
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
            if enablePillarLights:
                generateLightPillar (r, l, walls)
        elif l[1].getOn () == "FLOOR":
            if enableFloorLights:
                generateFloorLight (r, l, walls)
        elif l[1].getOn () == "CEIL":
            if enableCeilingLights:
                generateCeilingLight (r, l, walls)
        else:
            error ("unrecognised light position " + l[1].getOn ())


def generatePlinths (r):
    for p in rooms[r].plinths:
        pos = [int (p[0]), int (p[1]), getFloorLevel (r)]
        size = [1, 1, float (p[2]) / inchesPerUnit]
        print (pos, size)
        newcuboid (pos, size, 'plinth', r)


def generatePythonMonsters (o, e):
    n = 1
    for r in list(rooms.keys()):
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


def generateAmmo (o, e):
    n = 1
    for r in list(rooms.keys()):
        if debugging:
            print(rooms[r].ammo)
        for ammo_kind, a, xy in rooms[r].ammo:
            o.write ("// entity " + str (e) + '\n')
            o.write ("{\n")
            o.write ('    "inv_item" "4"\n')
            o.write ('    "classname" "' + ammo_kind + '"\n')
            o.write ('    "name" "' + ammo_kind + '_' + str (n) + '"\n')
            o.write ('    "origin" "')
            xyz = toIntList (xy) + [-invSpawnHeight]
            xyz = subVec (xyz, [minx, miny, getFloorLevel (r) + getPlinthHeight (r, xy[0], xy[1])])
            v = midReposition (xyz)
            o.write ('%f %f %f"\n' % (v[0], v[1], v[2]))
            o.write ("}\n")
            n += 1
            e += 1
    return o, e


def generateSounds (o, e):
    n = 1
    for r in list(rooms.keys()):
        if debugging:
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
        if debugging:
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
        if debugging:
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


def assignFloorLevel (f):
    global rooms
    for r in list(rooms.keys()):
        rooms[r].floorLevel = f


def generateMap (o):
    if genSteps:
        calcFloorLevel ()
    else:
        assignFloorLevel (0)
    o.write ("// automatically created from: " + inputFile + "\n")
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
    if statistics:
        print("Total rooms =", len (list(rooms.keys ())))
        print("Total cuboids =", len (list(cuboids.keys ())))
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


#
#  main - handle the input/output file options and call processMap.
#

def main ():
    global inputFile, words, toTxt
    io = handleOptions ()
    checkRegression ()
    if (io[0] == None) or (io[0] == '-'):
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

    words = lexicalPen (i)
    if parsePen ():
        if toTxt:
            o = generateTxt (o)
        else:
            o = generateMap (o)
        o.flush ()


main ()
