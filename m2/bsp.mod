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

IMPLEMENTATION MODULE bsp ;   (*!m2pim*)

FROM Storage IMPORT ALLOCATE ;
FROM nameKey IMPORT Name ;
FROM mapError IMPORT internalError ;

FROM Indexing IMPORT Index, InitIndex, GetIndice, PutIndice,
                     HighIndice, IncludeIndiceIntoIndex ;

TYPE
   def = POINTER TO RECORD
                       tag,
                       value: Name ;
                    END ;

   entity = POINTER TO RECORD
                          type  :  (unknown, patchdef2, brushdef3) ;
                          defs,
			  planes: Index ;
                       END ;

   plane = POINTER TO RECORD
                         normal : vec3 ;
			 dist   : LONGREAL ;
			 r0, r1 : vec3 ;
			 texture: Name ;
			 todo,
                         front,
			 back   : plane ;
                      END ;

VAR
   root,
   todo: plane ;


(*
   initEntity - creates an empty entity.
*)

PROCEDURE initEntity () : entity ;
VAR
   e: entity ;
BEGIN
   NEW (e) ;
   e^.type   := unknown ;
   e^.defs   := InitIndex (1) ;
   e^.planes := InitIndex (1) ;
   RETURN e
END initEntity ;


(*
   putBrushDef3 -
*)

PROCEDURE putBrushDef3 (e: entity) ;
BEGIN
   IF e^.type = unknown
   THEN
      e^.type := brushdef3
   ELSE
      internalError ('entity has already been defined',
                     __FILE__, __LINE__)
   END
END putBrushDef3 ;


(*
   putPatchDef2 -
*)

PROCEDURE putPatchDef2 (e: entity) ;
BEGIN
   IF e^.type = unknown
   THEN
      e^.type := patchdef2
   ELSE
      internalError ('entity has already been defined',
                     __FILE__, __LINE__)
   END
END putPatchDef2 ;


(*
   initPlane - creates and returns a new plane
               defined by the texture matrice
                  [r0,
                   r1,
                   [0.0, 0.0, 1.0]]
               mapped with, t.

               The plane is dist from the origin and is defined by,
               normal, value.  The texture image is defined by, t.
*)

PROCEDURE initPlane (normal: vec3; dist: LONGREAL; r0, r1: vec3; t: Name) : plane ;
VAR
   p: plane ;
BEGIN
   NEW (p) ;
   p^.normal := normal ;
   p^.dist := dist ;
   p^.r0 := r0 ;
   p^.r1 := r1 ;
   p^.texture := t ;
   p^.front := NIL ;
   p^.back := NIL ;
   p^.todo := todo ;
   todo := p ;
   RETURN p
END initPlane ;


(*
   includePlane - include plane, p, into entity, e.
*)

PROCEDURE includePlane (e: entity; p: plane) ;
BEGIN
   IncludeIndiceIntoIndex (e^.planes, p)
END includePlane ;


(*
   includeTags - include the tag [d:v] to entity, e.
                 d is the definition tag.
                 v is the value tag.
*)

PROCEDURE includeTags (e: entity; d, v: Name) ;
VAR
   p: def ;
BEGIN
   NEW (p) ;
   p^.tag := d ;
   p^.value := v ;
   IncludeIndiceIntoIndex (e^.defs, p)
END includeTags ;


PROCEDURE makeTree (polyList: polygon) : tree;
     VAR
	  root: polygon ;
	  backList, frontList: polygonP ;
	  p, backPart, frontPart: polygon ;

BEGIN
     IF polyList = NIL
     THEN
	  RETURN NIL
     ELSE
	  root := selectAndRemovePolygon (polyList) ;
	  backList := NIL ;
	  frontList := NIL ;
	  FOR p in polyList DO
	       IF p is in front of root
	       THEN
		    frontList := addToList (frontList, p)
	       ELSIF p is behind root
	       THEN
		    backList := addToList (backList, p)
	       ELSE
		    (* polygon, p, must be split as it spans across, root.  *)
		    splitPolygon (p, root, frontPart, backPart) ;
		    frontList := addToList (frontList, frontPart) ;
		    backList := addToList (backList, backPart) ;
	       END
	  END ;
	  RETURN combineTree (makeTree (frontList),
			      root,
			      makeTree (backList))
     END
END makeTree;


PROCEDURE generateBsp ;
BEGIN

END generateBsp;


(*
   init -
*)

PROCEDURE init ;
BEGIN
   root := NIL ;
   todo := NIL ;
END init ;


BEGIN
   init
END bsp.
