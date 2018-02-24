#!/usr/bin/env python

# Copyright (C) 2018
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

import getopt, sys, string


"""
EBNF of the pen file format

FileUnit := RoomDesc { RoomDesc } [ RandomTreasure ] "END." =:

RoomDesc := 'ROOM' Integer
            { WallDesc | DoorDesc | TreasureDesc } 'END' =:

WallDesc := 'WALL' WallCoords { WallCoords } =:

WallCoords := Integer Integer Integer Integer =:

DoorDesc := 'DOOR' DoorCoords { DoorCoords } =:

DoorCoords := Integer Integer Integer Integer Status
              'LEADS' 'TO' Integer
           =:

Status := 'STATUS' ( 'OPEN'
                      | 'CLOSED'
                      | 'SECRET'
                   )
       =:

TreasureDesc := 'TREASURE' 'AT' Integer Integer
                'IS' Integer
              =:

RandomTreasure := 'RANDOMIZE' 'TREASURE' Integer
                   { Integer }
               =:
"""

inputFile = None
defines = {}
verbose = False
debugging = False
toTxt = False
rooms = {}
maxx, maxy = 0, 0
doorValue, wallValue, emptyValue = 0, -1, -2
versionNumber = "0.1"
currentLineNo = 1
words = []
curStatus = None
status_open, status_closed, status_secret = range (3)
curRoom = None
curRoomNo = None
curPos = None
direction = ["left", "top", "right", "bottom"]
doorStatus = ["open", "closed", "secret"]
minx, miny, minz = None, None, None
defaultOn = "MID"
curOn = defaultOn


#
#  mycut - return a list, l, which is broken into three pieces.
#          [0 .. i-1], [i], [i+1 .. end]
#
#          Some of the pieces might be None if, i, is at either end
#          of the list.
#

def mycut (l, i):
    if i == 0:
        if len (l) > 1:
            return None, l[i], l[i+1:]
        return None, l[i], None
    if len (l) > i+1:
        return l[:i], l[i], l[i+1:]
    return l[:i], l[i], None


#
#  mystitch - combines lists, a, b, c, together and returns the result.
#             It will ignore any a, b, c, which is None.
#             Pre-condition : a, b, c, are lists or are a or c might be None.
#             Post-condition: [a + b + c]   ignoring any None.
#

def mystitch (a, b, c):
    if a == None:
        d = b
    else:
        d = a + b
    if c == None:
        return d
    return d + c


#
#  setFloor - Pre-condition:  None.
#             Post-condition: sets array:
#
#                floor[x, y] := value
#

def setFloor (x, y, value):
    global floor
    a, b, c = mycut (floor, y)
    x, y, z = mycut (b, x)
    b = mystitch (x, [value], z)
    floor = mystitch (a, [b], c)


#
#  getFloor - Pre-condition:  floor[x, y] must exist and be in range
#                 see initFloor.
#             must have been called beforehand.
#             Post-condition: returns floor[x, y]
#

def getFloor (x, y):
    global floor
    return floor[y][x]


#
#  initFloor - initialise an empty array of dimensions, x, y, with a, value.
#

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
#  roomInfo - the class which will be used to contain the map.
#

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

    #
    #  addWall - Pre-condition:  line is a list of two elements.
    #            Each element is a list of two numbers, each number is a string.
    #            Post-condition: The line is converted to a list of two elements,
    #              each element is a list of two integers.  This list is added to
    #              the list of walls.
    #

    def addWall (self, line):
        global maxx, maxy
        line = toLine (line)
        self.walls += [line]
        maxx = max (line[0][0], maxx)
        maxx = max (line[1][0], maxx)
        maxy = max (line[0][1], maxy)
        maxy = max (line[1][1], maxy)

    #
    #  addDoor - Pre-condition:  line is converted into an integer point line.
    #            The door defined by the [point line, leadsto, status]
    #            Post-condition:  the door is added to the doors list.
    #

    def addDoor (self, line, leadsto, status):
        self.doors += [[toLine (line), leadsto, status]]

    #
    #  addAmmo - Pre-condition:  None.
    #            Post-condition:  ammo list extended to contain a new element
    #                             [ammoType, ammoAmount, ammoPos].
    #

    def addAmmo (self, ammoType, ammoAmount, ammoPos):
        self.ammo += [[ammoType, ammoAmount, ammoPos]]

    #
    #  addLight - Pre-condition:  None.
    #             Post-condition:  add [pos, col, on] to the list of lights.
    #

    def addLight (self, pos, col, on):
        self.lights += [[pos, col, on]]
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

def newRoom (n):
    global rooms
    if rooms.has_key (n):
        error ("room " + n + " has already been defined")
    rooms[n] = roomInfo (n, [], [])
    return rooms[n]


#
#  printf - keeps C programmers happy :-)
#

def printf (format, *args):
    print str(format) % args,


#
#  error - issues an error message and exits.
#

def error (format, *args):
    print str (format) % args,
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
        print str (format) % args,


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
            print "cannot open file", name, "to read the default textures as requested"
            sys.exit (1)


def usage (code):
    print "Usage: pen2map [-c filename.ss] [-defhmtvV] [-o outputfile] inputfile"
    print "  -d                debugging"
    print "  -h                help"
    print "  -t                create a txt file from the pen file"
    print "  -V                generate verbose information"
    print "  -v                print the version"
    print "  -o outputfile     place output into outputfile"
    sys.exit (code)


#
#  handleOptions -
#

def handleOptions ():
    global debugging, verbose, outputName, toTxt

    outputName = None
    try:
        optlist, l = getopt.getopt(sys.argv[1:], ':bc:defg:hmo:rstvVO')
        for opt in optlist:
            if opt[0] == '-d':
                debugging = True
            elif opt[0] == '-h':
                usage (0)
            elif opt[0] == '-o':
                outputName = opt[1]
            elif opt[0] == '-v':
                printf ("pen2pen version %s\n", versionNumber)
                sys.exit (0)
            elif opt[0] == '-t':
                toTxt = True
            elif opt[0] == '-V':
                verbose = True
        if l != []:
            return (l[0], outputName)
        print "you need to supply an input file or use - for stdin"
        usage (1)

    except getopt.GetoptError:
       usage (1)
    return (None, outputName)


def errorLine (text):
    global inputFile, currentLineNo
    full = "%s:%d:%s\n" % (inputFile, currentLineNo, text)
    print full
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
            print "will start"
        else:
            print "will not start", getFloor (p[0], p[1])
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


def wallDesc ():
    expect ('WALL')
    if wallCoords ():
        while wallCoords ():
            pass


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
            curStatus = status_open    # --fixme-- secret doors would be nice!
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
    if i.isdigit ():
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
#  colDesc - returns True if colour int int int is seen.
#

def colDesc ():
    global curCol
    if expecting (['COLOUR']):
        expect ('COLOUR')
        curCol = []
        if integer ():
            curCol += [curInteger]
            if integer ():
                curCol += [curInteger]
                if integer ():
                    curCol += [curInteger]
                    return True
                else:
                    errorLine ('expecting green colour component')
            else:
                errorLine ('expecting blue colour component')
        else:
            errorLine ('expecting red colour component')
    return False


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
        if curRoom.defaultColours.has_key (curOn):
            return curRoom.defaultColours[curOn]
        return defaultColour
    return col


#
#  scopeColourRoom - return the default colour for a room or global default colour
#                    if one has not been defined.
#

def scopeColourRoom (r, on):
    if rooms[r].defaultColours.has_key (on):
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
        if colDesc ():
            pass
        if onDesc ():
            pass
        curRoom.addLight (curPos, curCol, curOn)
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
#  weaponDesc := 'LIGHT' 'AT' posDesc =:
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
#  defaultDesc := "DEFAULT" ( "CEIL" | "MID" | "FLOOR" ) "COLOUR" int int int =:
#

def defaultDesc ():
    expect ("DEFAULT")
    if expecting (['FLOOR']):
        expect ('FLOOR')
        colDesc ()
        curRoom.defaultColours['FLOOR'] = curCol
    elif expecting (['MID']):
        expect ('MID')
        colDesc ()
        curRoom.defaultColours['MID'] = curCol
    elif expecting (['CEIL']):
        expect ('CEIL')
        colDesc ()
        curRoom.defaultColours['CEIL'] = curCol
    else:
        errorLine ("expecting FLOOR, MID or CEILING after DEFAULT")


#
#  roomDesc := "ROOM" integer { doorDesc | wallDesc | treasureDesc | ammoDesc | lightDesc | insideDesc | weaponDesc | monsterDesc | spawnDesc } =:
#

def roomDesc ():
    global curRoom, curInteger, curRoomNo, verbose
    if expecting (['ROOM']):
        expect ("ROOM")
        if integer ():
            curRoomNo = curInteger
            curRoom = newRoom (curRoomNo)
            if verbose:
                print "roomDesc", curRoomNo
            while expecting (['DOOR', 'WALL', 'TREASURE', 'AMMO', 'WEAPON', 'LIGHT', 'INSIDE', 'MONSTER', 'SPAWN', 'DEFAULT']):
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
                elif expecting (['LIGHT']):
                    lightDesc ()
                elif expecting (['INSIDE']):
                    insideDesc ()
                elif expecting (['WEAPON']):
                    weaponDesc ()
                elif expecting (['MONSTER']):
                    monsterDesc ()
                elif expecting (['SPAWN']):
                    spawnDesc ()
                elif expecting (['DEFAULT']):
                    defaultDesc ()
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
            plotLine (d[0], '%')


#
#  generateTxt - generate an ascii .txt file containing the map.
#

def generateTxt (o):
    initFloor (maxx, maxy, ' ')
    for r in rooms.keys ():
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
    print "w =", w
    print "e =", e
    print "p =", p
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
        print "orderWalls, entered"
        for i in w:
            print i
    n = []
    i = findLowestLeftVertical (w)
    if debugging:
        print "findLowestLeftVertical =", i
    n += [sortWall (w[i])]
    e = getHighest (w[i])
    if debugging:
        print "w[i] =", w[i], "e =", e
    p = [getLowest (w[i])]
    if debugging:
        print "i =", i
        print "w =", w
        print "n =", n
        print "i =", i
        print "p =", p
        print "loop"
    del w[i]
    while w != []:
        i = findJoining (r, w, e, p)
        n += [sortWall (w[i])]
        if debugging:
            print "i =", i
            print "n =", n
            print "2nd p =", p
            print "w =", w
        p = include (p, w[i][0])
        p = include (p, w[i][1])
        if e == w[i][0]:
            e = w[i][1]
        else:
            e = w[i][0]
        if debugging:
            print "3rd p =", p, "e =", e
        del w[i]
    if debugging:
        print "orderWalls, exiting with", n
    if not isVertical (n[0]):
        internalError ('expecting first wall to be vertical')
    return n


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
        print "sortwall", w
    if isVertical (w):
        if w[0][1] > w[1][1]:
            return [w[1], w[0]]
        return w
    if isHorizontal (w):
        if w[0][0] > w[1][0]:
            return [w[1], w[0]]
        return w
    print "wall problem", w
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
        print "entityWall", start, end, d
    if isHorizontal ([start, end]) or isVertical ([start, end]):
        return [[start, end, "wall", direction[d]]]
    print start, end, "direction d=", d
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
            print w, i
            internalError ('wallToEntity: expecting wall to be vertical')
    elif (i == 1) or (i == 3):
        if not isHorizontal (w):
            print w, i
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
        print "room", r, "has a problem with a wall, ", w, "p is not on either end", p
        sys.exit (1)


def createWallDoorList (r, walls, doors):
    if debugging:
        print "createWallDoorList"
        print "=================="
        print "room", r, "has walls"
        for i in walls:
            print i
        print "room", r, "has doors"
        for i in doors:
            print i
    e = []
    d = 0   # direction is left
    p = walls[0][0]
    if debugging:
        print "lowest left, p =", p
    for i, w in enumerate (walls):
        if debugging:
            print "direction", d, "position", p, "looking at", w
        checkOnWall (r, p, w)
        if (d == 0) or (d == 2):
            # on left or right vertical wall
            if movesRight (w, p):
                d = 1  # from left to top wall
                if debugging:
                    print "moves to top because of wall", w
            elif movesLeft (w, p):
                d = 3  # from left to bottom wall
                if debugging:
                    print "moves to bottom because of wall", w
        else:
            # must be on either top or bottom wall
            if movesUp (w, p):
                d = 0  # from top/bottom to left vertical wall
                if debugging:
                    print "moves to left because of wall", w
            elif movesDown (w, p):
                d = 2  # from top/bottom to right vertical wall
                if debugging:
                    print "moves to right because of wall", w
        if (d == 0) or (d == 2):
            if not isVertical (w):
                print w, d
                internalError ('createWallDoorList: expecting wall to be vertical')
        elif (d == 1) or (d == 3):
            if not isHorizontal (w):
                print w, d
                internalError ('createWallDoorList: expecting wall to be horizontal')

        e += wallToEntity (w, d, doors)
        if equVec (p, w[0]):
            p = w[1]
        else:
            p = w[0]
        if debugging:
            print "entity list", e
    if debugging:
        print "entity list is", e
    return e


def roomToEntities (r):
    w = orderWalls (r, rooms[r].walls)
    if debugging:
        print "ordered walls =", w
    return createWallDoorList (r, w, rooms[r].doors)


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


#
#  findOffsetInRoom - scans room, r, for the minx, miny, values.
#

def findOffsetInRoom (r):
    global minx, miny
    for e in rooms[r].walls:
        if minx == None:
            minx = int (e[0][0])
        else:
            minx = min (int (e[0][0]), minx)
        if miny == None:
            miny = int (e[0][1])
        else:
            miny = min (miny, int (e[0][1]))


#
#   findOffsets - determine the minx, miny, in the complete map.
#

def findOffsets ():
    for r in rooms.keys ():
        findOffsetInRoom (r)


#
#  getSpawnRoom - return the room in which the player is spawned.
#

def getSpawnRoom ():
    for r in rooms.keys ():
        if rooms[r].worldspawn != []:
            return r
    return None

#
#  getListOfRooms - return the complete list of rooms.
#

def getListOfRooms ():
    return rooms.keys ()

#
#  getNeighbours - return the neighbouring rooms for room, r.
#

def getNeighbours (r):
    n = []
    for d in r.doors:
        n += [d[1]]
    return n


def generatePen (o):
    return o


#
#  main - handle the input/output file options and call processMap.
#

def main ():
    global inputFile, words, toTxt
    io = handleOptions ()
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
            o = generatePen (o)
        o.flush ()


main ()
