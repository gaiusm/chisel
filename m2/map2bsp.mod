(* Copyright (C) 2017 Free Software Foundation, Inc.  *)
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
Foundation, 51 Franklin Street, Fifth Floor,
Boston, MA 02110-1301, USA.  *)

MODULE map2bsp ;   (*!m2pim*)

FROM SArgs IMPORT GetArg, Narg ;
FROM DynamicStrings IMPORT String, Dup, EqualArray, string ;
FROM libc IMPORT printf, exit ;
FROM parser IMPORT compile ;
FROM mapflex IMPORT openSource ;
FROM mapOptions IMPORT setDebugging ;


(*
   usage -
*)

PROCEDURE usage (e: INTEGER) ;
BEGIN
   printf ("usage:  map2bsp inputfile.map [-p outputfile.proc] [-c outputfile.cm] [-h] [-d] [-s]\n") ;
   printf ("        -h  help\n") ;
   printf ("        -p  output file name of the .proc file\n") ;
   printf ("        -c  output file name of the .cm file\n") ;
   printf ("        -d  turn on internal debugging\n") ;
   printf ("        -s  display statistics\n") ;
   printf ("        -v  display version\n") ;
   exit (e)
END usage ;


(*
   getNext -
*)

PROCEDURE getNext (i: CARDINAL) : String ;
VAR
   s: String ;
BEGIN
   IF GetArg (s, i+1)
   THEN
      RETURN s
   ELSE
      RETURN NIL
   END
END getNext ;


(*
   init -
*)

PROCEDURE init ;
VAR
   i         : CARDINAL ;
   s,
   inputName,
   outputName: String ;
BEGIN
   IF Narg () < 2
   THEN
      usage (0)
   ELSE
      i := 1 ;
      inputName := NIL ;
      WHILE GetArg (s, i) DO
         IF EqualArray (s, '-o')
         THEN
            outputName := getNext (i) ;
	    INC (i)
         ELSIF EqualArray (s, '-d')
         THEN
            setDebugging (TRUE)
         ELSIF EqualArray (s, '-h')
         THEN
            usage (0)
         ELSE
            inputName := Dup (s)
         END ;
         INC (i)
      END ;
      IF inputName = NIL
      THEN
         printf ("map2bsp requires an input filename\n") ;
	 usage (1)
      END ;
      s := string (inputName) ;
      IF openSource (inputName)
      THEN
         printf ("compiling: %s\n", s) ;
         IF compile ()
         THEN

         END
      ELSE
         printf ("cannot open input file: %s\n", s)
      END
   END
END init ;


BEGIN
   init
END map2bsp.
