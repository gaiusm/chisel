(* Copyright (C) 2015, 2016, 2017
                 Free Software Foundation, Inc.  *)
(* This file is part of Chisel.

Chisel is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free
Software Foundation; either version 3, or (at your option) any later
version.

Chisel is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
for more details.

You should have received a copy of the GNU General Public License along
with gm2; see the file COPYING.  If not, write to the Free Software
Foundation, 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.  *)

IMPLEMENTATION MODULE mapError ;

FROM ASCII IMPORT nul, nl ;
FROM DynamicStrings IMPORT String, InitString, InitStringCharStar, ConCat, ConCatChar, Mark, string, KillString, Dup ;
FROM FIO IMPORT StdOut, WriteNBytes, Close, FlushBuffer ;
FROM StrLib IMPORT StrLen, StrEqual ;
FROM FormatStrings IMPORT Sprintf0, Sprintf1, Sprintf2, Sprintf3 ;
FROM Storage IMPORT ALLOCATE, DEALLOCATE ;
FROM M2RTS IMPORT ExitOnHalt ;
FROM SYSTEM IMPORT ADDRESS ;
FROM mapflex IMPORT getFileName, getLineNo, getColumnNo ;

IMPORT StdIO ;


CONST
   Debugging  =  TRUE ;
   DebugTrace = FALSE ;

VAR
   inInternal: BOOLEAN ;



(*
   outString - writes the contents of String to stdout.
               The string, s, is destroyed.
*)

PROCEDURE outString (file: String; line, col: CARDINAL; s: String) ;
VAR
   leader : String ;
   p, q   : POINTER TO CHAR ;
   space,
   newline: BOOLEAN ;
BEGIN
   INC (col) ;
   leader := Sprintf3(Mark(InitString('%s:%d:%d:')), file, line, col) ;
   p := string(s) ;
   newline := TRUE ;
   space := FALSE ;
   WHILE (p#NIL) AND (p^#nul) DO
      IF newline
      THEN
         q := string (leader) ;
         WHILE (q#NIL) AND (q^#nul) DO
            StdIO.Write (q^) ;
            INC (q)
         END
      END ;
      newline := (p^=nl) ;
      space := (p^=' ') ;
      StdIO.Write (p^) ;
      INC (p)
   END ;
   IF NOT newline
   THEN
      StdIO.Write (nl)
   END ;
   FlushBuffer (StdOut) ;
   IF NOT Debugging
   THEN
      s      := KillString (s) ;
      leader := KillString (leader)
   END
END outString ;


(*
   internalError - displays an internal error message together with the compiler source
                   file and line number.
                   This function is not buffered and is used when the compiler is about
                   to give up.
*)

PROCEDURE internalError (a: ARRAY OF CHAR; file: ARRAY OF CHAR; line: CARDINAL) ;
BEGIN
   ExitOnHalt (1) ;
   IF NOT inInternal
   THEN
      inInternal := TRUE ;
      outString (InitStringCharStar (getFileName ()),
                 getLineNo (),
                 getColumnNo (),
                 Mark(InitString ('*** fatal error ***')))
   END ;
   outString (Mark (InitString (file)), line, 0,
              ConCat (Mark (InitString('*** internal error *** ')), Mark (InitString (a)))) ;
   HALT
END internalError ;


(*
   errorString - display error message, s.
*)

PROCEDURE errorString (s: String) ;
BEGIN
   outString (InitStringCharStar (getFileName ()),
              getLineNo (),
              getColumnNo (),
              s)
END errorString ;


(*
   init - initialise all module data structures.
*)

PROCEDURE init ;
BEGIN
   inInternal := FALSE
END init ;


BEGIN
   init
END mapError.
