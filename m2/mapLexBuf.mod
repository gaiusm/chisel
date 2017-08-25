(* Copyright (C) 2017
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

IMPLEMENTATION MODULE mapLexBuf ;

IMPORT mapflex ;

FROM libc IMPORT strlen, printf ;
FROM SYSTEM IMPORT ADDRESS ;
FROM Storage IMPORT ALLOCATE, DEALLOCATE ;
FROM DynamicStrings IMPORT string, InitString, InitStringCharStar, Equal, Mark, KillString ;
FROM FormatStrings IMPORT Sprintf1 ;
FROM nameKey IMPORT NulName, Name, makekey, keyToCharStar ;
FROM mapflex IMPORT toktype ;
FROM mapDebug IMPORT assert ;


CONST
   MaxBucketSize = 100 ;
   Debugging     = FALSE ;

TYPE
   sourceList = POINTER TO RECORD
                              left,
                              right: sourceList ;
                              name : String ;
                              line : CARDINAL ;
                              col  : CARDINAL ;
                           END ;

   tokenDesc = RECORD
                  token: toktype ;
                  str  : Name ;
                  int  : INTEGER ;
                  line : CARDINAL ;
                  col  : CARDINAL ;
                  file : sourceList ;
               END ;

   tokenBucket = POINTER TO RECORD
                               buf : ARRAY [0..MaxBucketSize] OF tokenDesc ;
                               len : CARDINAL ;
                               next: tokenBucket ;
                            END ;

   listDesc = RECORD
                 head,
                 tail            : tokenBucket ;
                 lastBucketOffset: CARDINAL ;
              END ;

VAR
   currentSource    : sourceList ;
   currentUsed      : BOOLEAN ;
   listOfTokens     : listDesc ;
   currentTokNo     : CARDINAL ;



(*
   init - initializes the token list and source list.
*)

PROCEDURE init ;
BEGIN
   currenttoken := eoftok ;
   currentTokNo := 0 ;
   currentSource := NIL ;
   listOfTokens.head := NIL ;
   listOfTokens.tail := NIL ;
END init ;


(*
   addTo - adds a new element to the end of sourceList, currentSource.
*)

PROCEDURE addTo (l: sourceList) ;
BEGIN
   l^.right := currentSource ;
   l^.left  := currentSource^.left ;
   currentSource^.left^.right := l ;
   currentSource^.left := l ;
   WITH l^.left^ DO
      line := mapflex.getLineNo() ;
      col  := mapflex.getColumnNo()
   END
END addTo ;


(*
   subFrom - subtracts, l, from the source list.
*)

PROCEDURE subFrom (l: sourceList) ;
BEGIN
   l^.left^.right := l^.right ;
   l^.right^.left := l^.left
END subFrom ;


(*
   newElement - returns a new sourceList
*)

PROCEDURE newElement (s: ADDRESS) : sourceList ;
VAR
   l: sourceList ;
BEGIN
   NEW (l) ;
   IF l=NIL
   THEN
      HALT
   ELSE
      WITH l^ DO
         name  := InitStringCharStar (s) ;
         left  := NIL ;
         right := NIL
      END
   END ;
   RETURN l
END newElement ;


(*
   newList - initializes an empty list with the classic dummy header element.
*)

PROCEDURE newList () : sourceList ;
VAR
   l: sourceList ;
BEGIN
   NEW (l) ;
   WITH l^ DO
      left  := l ;
      right := l ;
      name  := NIL
   END ;
   RETURN l
END newList ;


(*
   checkIfNeedToDuplicate - checks to see whether the currentSource has
                            been used, if it has then duplicate the list.
*)

PROCEDURE checkIfNeedToDuplicate ;
VAR
   l, h: sourceList ;
BEGIN
   IF currentUsed
   THEN
      l := currentSource^.right ;
      h := currentSource ;
      currentSource := newList() ;
      WHILE l#h DO
         addTo (newElement (l^.name)) ;
         l := l^.right
      END
   END
END checkIfNeedToDuplicate ;


(*
   setFile - sets the current filename to, filename.
*)

PROCEDURE setFile (filename: ADDRESS) ;
BEGIN
   currentUsed   := FALSE ;
   currentSource := newList() ;
   addTo (newElement (filename))
END setFile ;


(*
   openSource - attempts to open the source file, s.
                The success of the operation is returned.
*)

PROCEDURE openSource (s: String) : BOOLEAN ;
BEGIN
   IF mapflex.openSource (string (s))
   THEN
      setFile (string (s)) ;
      syncOpenWithBuffer ;
      getToken ;
      RETURN TRUE
   ELSE
      RETURN FALSE
   END
END openSource ;


(*
   closeSource - closes the current open file.
*)

PROCEDURE closeSource ;
BEGIN
   (* a no op  *)
END closeSource ;


(*
   updateFromBucket - updates the global variables:  currenttoken,
                      currentstring, currentcolumn and currentinteger
                      from tokenBucket, b, and, offset.
*)

PROCEDURE updateFromBucket (b: tokenBucket; offset: CARDINAL) ;
BEGIN
   WITH b^.buf[offset] DO
      currenttoken   := token ;
      currentstring  := keyToCharStar (str) ;
      currentcolumn  := col ;
      currentinteger := int ;
      IF Debugging
      THEN
         printf ('line %d (# %d  %d) ', line, offset, currentTokNo)
      END
   END
END updateFromBucket ;


(*
   getToken - gets the next token into currenttoken.
*)

PROCEDURE getToken ;
VAR
   a: ADDRESS ;
   t: CARDINAL ;
   b: tokenBucket ;
BEGIN
   IF listOfTokens.tail=NIL
   THEN
      a := mapflex.getToken () ;
      IF listOfTokens.tail=NIL
      THEN
         HALT
      END
   END ;
   IF currentTokNo>=listOfTokens.lastBucketOffset
   THEN
      (* currentTokNo is in the last bucket or needs to be read.  *)
      IF currentTokNo-listOfTokens.lastBucketOffset<listOfTokens.tail^.len
      THEN
         updateFromBucket (listOfTokens.tail,
                           currentTokNo-listOfTokens.lastBucketOffset)
      ELSE
         (* call the lexical phase to place a new token into the last bucket.  *)
         a := mapflex.getToken () ;
         getToken ; (* and call ourselves again to collect the token from bucket.  *)
         RETURN
      END
   ELSE
      t := currentTokNo ;
      b := findtokenBucket (t) ;
      updateFromBucket (b, t)
   END ;
   INC (currentTokNo)
END getToken ;


(*
   syncOpenWithBuffer - synchronise the buffer with the start of a file.
                        Skips all the tokens to do with the previous file.
*)

PROCEDURE syncOpenWithBuffer ;
BEGIN
   IF listOfTokens.tail#NIL
   THEN
      WITH listOfTokens.tail^ DO
         currentTokNo := listOfTokens.lastBucketOffset+len
      END
   END
END syncOpenWithBuffer ;


(*
   insertToken - inserts a symbol, token, infront of the current token
                 ready for the next pass.
*)

PROCEDURE insertToken (token: toktype) ;
BEGIN
   IF listOfTokens.tail#NIL
   THEN
      WITH listOfTokens.tail^ DO
         IF len>0
         THEN
            buf[len-1].token := token
         END
      END ;
      addTokToList (currenttoken, NulName, 0,
                    getLineNo (), getColumnNo (), currentSource) ;
      getToken
   END
END insertToken ;


(*
   getLineNo - returns the current line number where the symbol occurs in
               the source file.
*)

PROCEDURE getLineNo () : CARDINAL ;
BEGIN
   IF currentTokNo=0
   THEN
      RETURN 0
   ELSE
      RETURN tokenToLineNo (getTokenNo (), 0)
   END
END getLineNo ;


(*
   getColumnNo - returns the current column where the symbol occurs in
                 the source file.
*)

PROCEDURE getColumnNo () : CARDINAL ;
BEGIN
   IF currentTokNo=0
   THEN
      RETURN 0
   ELSE
      RETURN tokenToColumnNo (getTokenNo (), 0)
   END
END getColumnNo ;


(*
   getTokenNo - returns the current token number.
*)

PROCEDURE getTokenNo () : CARDINAL ;
BEGIN
   IF currentTokNo=0
   THEN
      RETURN 0
   ELSE
      RETURN currentTokNo-1
   END
END getTokenNo ;


(*
   findtokenBucket - returns the tokenBucket corresponding to the tokenNo.
*)

PROCEDURE findtokenBucket (VAR tokenNo: CARDINAL) : tokenBucket ;
VAR
   b: tokenBucket ;
BEGIN
   b := listOfTokens.head ;
   WHILE b#NIL DO
      WITH b^ DO
         IF tokenNo<len
         THEN
            RETURN b
         ELSE
            DEC (tokenNo, len)
         END
      END ;
      b := b^.next
   END ;
   RETURN NIL
END findtokenBucket ;


(*
   tokenToLineNo - returns the line number of the current file for the
                   tokenNo.  The depth refers to the include depth.
                   A depth of 0 is the current file, depth of 1 is the file
                   which included the current file.  Zero is returned if the
                   depth exceeds the file nesting level.
*)

PROCEDURE tokenToLineNo (tokenNo: CARDINAL; depth: CARDINAL) : CARDINAL ;
VAR
   b: tokenBucket ;
   l: sourceList ;
BEGIN
   b := findtokenBucket (tokenNo) ;
   IF b=NIL
   THEN
      RETURN 0
   ELSE
      IF depth=0
      THEN
         RETURN b^.buf[tokenNo].line
      ELSE
         l := b^.buf[tokenNo].file^.left ;
         WHILE depth>0 DO
            l := l^.left ;
            IF l=b^.buf[tokenNo].file^.left
            THEN
               RETURN 0
            END ;
            DEC (depth)
         END ;
         RETURN l^.line
      END
   END
END tokenToLineNo ;


(*
   tokenToColumnNo - returns the column number of the current file for the
                     tokenNo. The depth refers to the include depth.
                     A depth of 0 is the current file, depth of 1 is the file
                     which included the current file. Zero is returned if the
                     depth exceeds the file nesting level.
*)

PROCEDURE tokenToColumnNo (tokenNo: CARDINAL; depth: CARDINAL) : CARDINAL ;
VAR
   b: tokenBucket ;
   l: sourceList ;
BEGIN
   b := findtokenBucket (tokenNo) ;
   IF b=NIL
   THEN
      RETURN 0
   ELSE
      IF depth=0
      THEN
         RETURN b^.buf[tokenNo].col
      ELSE
         l := b^.buf[tokenNo].file^.left ;
         WHILE depth>0 DO
            l := l^.left ;
            IF l=b^.buf[tokenNo].file^.left
            THEN
               RETURN 0
            END ;
            DEC (depth)
         END ;
         RETURN l^.col
      END
   END
END tokenToColumnNo ;


(*
   findFileNameFromToken - returns the complete FileName for the appropriate
                           source file yields the token number, tokenNo.
                           The, Depth, indicates the include level: 0..n
                           Level 0 is the current. NIL is returned if n+1
                           is requested.
*)

PROCEDURE findFileNameFromToken (tokenNo: CARDINAL; depth: CARDINAL) : String ;
VAR
   b: tokenBucket ;
   l: sourceList ;
BEGIN
   b := findtokenBucket (tokenNo) ;
   IF b=NIL
   THEN
      RETURN NIL
   ELSE
      l := b^.buf[tokenNo].file^.left ;
      WHILE depth>0 DO
         l := l^.left ;
         IF l=b^.buf[tokenNo].file^.left
         THEN
            RETURN NIL
         END ;
         DEC (depth)
      END ;
      RETURN l^.name
   END
END findFileNameFromToken ;


(*
   getFileName - returns a String defining the current file.
*)

PROCEDURE getFileName () : String ;
BEGIN
   RETURN findFileNameFromToken (getTokenNo (), 0)
END getFileName ;


PROCEDURE stop ; BEGIN END stop ;


(*
   addTokToList - adds a token to a dynamic list.
*)

PROCEDURE addTokToList (t: toktype; n: Name;
                        i: INTEGER; l: CARDINAL; c: CARDINAL; f: sourceList) ;
VAR
   b: tokenBucket ;
BEGIN
   IF listOfTokens.head=NIL
   THEN
      NEW (listOfTokens.head) ;
      IF listOfTokens.head=NIL
      THEN
         (* list error *)
      END ;
      listOfTokens.tail := listOfTokens.head ;
      listOfTokens.tail^.len := 0
   ELSIF listOfTokens.tail^.len=MaxBucketSize
   THEN
      assert (listOfTokens.tail^.next=NIL) ;
      NEW (listOfTokens.tail^.next) ;
      IF listOfTokens.tail^.next=NIL
      THEN
         (* list error *)
      ELSE
         listOfTokens.tail := listOfTokens.tail^.next ;
         listOfTokens.tail^.len := 0
      END ;
      INC (listOfTokens.lastBucketOffset, MaxBucketSize)
   END ;
   WITH listOfTokens.tail^ DO
      next := NIL ;
      WITH buf[len] DO
         token := t ;
         str   := n ;
         int   := i ;
         line  := l ;
         col   := c ;
         file  := f
      END ;
      INC (len)
   END
END addTokToList ;


(*
   isLastTokenEof - returns TRUE if the last token was an eoftok
*)

PROCEDURE isLastTokenEof () : BOOLEAN ;
VAR
   t: CARDINAL ;
   b: tokenBucket ;
BEGIN
   IF listOfTokens.tail#NIL
   THEN
      IF listOfTokens.tail^.len=0
      THEN
         b := listOfTokens.head ;
         IF b=listOfTokens.tail
         THEN
            RETURN FALSE
         END ;
         WHILE b^.next#listOfTokens.tail DO
            b := b^.next
         END ;
      ELSE
         b := listOfTokens.tail
      END ;
      WITH b^ DO
         assert (len>0) ;     (* len should always be >0 *)
         RETURN buf[len-1].token=eoftok
      END
   END ;
   RETURN FALSE
END isLastTokenEof ;


(* ***********************************************************************
 *
 * These functions allow m2.flex to deliver tokens into the buffer
 *
 ************************************************************************* *)

(*
   addTok - adds a token to the buffer.
*)

PROCEDURE addTok (t: toktype) ;
BEGIN
   IF NOT ((t=eoftok) AND isLastTokenEof())
   THEN
      addTokToList (t, NulName, 0,
                    mapflex.getLineNo (), mapflex.getColumnNo (), currentSource) ;
      currentUsed := TRUE
   END
END addTok ;


(*
   addTokCharStar - adds a token to the buffer and an additional string, s.
                    A copy of string, s, is made.
*)

PROCEDURE addTokCharStar (t: toktype; s: ADDRESS) ;
BEGIN
   IF strlen(s)>80
   THEN
      stop
   END ;
   addTokToList (t, makekey (s), 0, mapflex.getLineNo (),
                 mapflex.getColumnNo (), currentSource) ;
   currentUsed := TRUE
END addTokCharStar ;


(*
   addTokInteger - adds a token and an integer to the buffer.
*)

PROCEDURE addTokInteger (t: toktype; i: INTEGER) ;
VAR
   s: String ;
   c,
   l: CARDINAL ;
BEGIN
   l := mapflex.getLineNo () ;
   c := mapflex.getColumnNo () ;
   s := Sprintf1 (Mark (InitString ('%d')), i) ;
   addTokToList (t, makekey(string(s)), i, l, c, currentSource) ;
   s := KillString (s) ;
   currentUsed := TRUE
END addTokInteger ;


BEGIN
   init
END mapLexBuf.
