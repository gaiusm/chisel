(* Copyright (C) 2015 Free Software Foundation, Inc.  *)
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

IMPLEMENTATION MODULE vector3 ;   (*!m2pim*)


(*
   initVec3 - initialise the fields of a vec3 to x, y, z.
*)

PROCEDURE initVec3 (x, y, z: LONGREAL) : vec3 ;
VAR
   v: vec3 ;
BEGIN
   v.x := x ;
   v.y := y ;
   v.z := z ;
   RETURN v
END initVec3 ;


END vector3.
