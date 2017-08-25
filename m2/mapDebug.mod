(* Copyright (C) 2015,
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

IMPLEMENTATION MODULE mapDebug ;


FROM StrIO IMPORT WriteString, WriteLn ;
FROM mapOptions IMPORT debugging ;
FROM mapError IMPORT internalError ;


(*
   assert - tests the boolean, q. If false then an error is reported
            and the execution is terminated.
*)

PROCEDURE assert (q: BOOLEAN) ;
BEGIN
   IF NOT q
   THEN
      internalError ('assert failed', __FILE__, __LINE__)
   END
END assert ;


(*
   writeDebug - only writes a string if internal debugging is on.
*)

PROCEDURE writeDebug (a: ARRAY OF CHAR) ;
BEGIN
   IF debugging ()
   THEN
      WriteString (a) ; WriteLn
   END
END writeDebug ;


END mapDebug.
