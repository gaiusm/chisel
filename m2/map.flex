%{
/* Copyright (C) 2017 Free Software Foundation, Inc.
   This file is part of Chisel.

Chisel is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free
Software Foundation; either version 2, or (at your option) any later
version.

Chisel is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
for more details.

You should have received a copy of the GNU General Public License along
with gm2; see the file COPYING.  If not, write to the Free Software
Foundation, 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 */

#include <stdio.h>

  /*
   *  map.flex - provides a lexical analyser for map files
   */

  struct lineInfo {
    char            *linebuf;          /* line contents */
    int              linelen;          /* length */
    int              tokenpos;         /* start position of token within line */
    int              toklen;           /* a copy of yylen (length of token) */
    int              nextpos;          /* position after token */
    int              actualline;       /* line number of this line */
    int              column;           /* first column number of token on this line */
  };

  static int                  lineno      =1;   /* a running count of the file line number */
  static char                *filename    =NULL;
  static struct lineInfo     *currentLine =NULL;

        void mapflex_error      (const char *);
static  void finishedLine       (void);
static  void resetpos           (void);
static  void consumeLine        (void);
static  void updatepos          (int);
static  void skippos            (void);
static  void poperrorskip       (const char *);
	int  mapflex_openSource (char *s);
	int  mapflex_getLineNo  (void);
	void mapflex_closeSource(void);
	void mapflex_getToken  (void);
        char *mapflex_getFileName (void);
        void _M2_mapflex_init   (void);
extern  void  yylex             (void);
extern  int  mapOptions_debugging (void);

#if !defined(TRUE)
#    define TRUE  (1==1)
#endif
#if !defined(FALSE)
#    define FALSE (1==0)
#endif

typedef enum {eoftok, versiontok,
              lcbratok, rcbratok,    /* { and }  */
	      lrbratok, rrbratok,    /* ( and )  */
	      brushdef3tok, patchdef2tok,
	      integertok,
	      identtok, longrealtok,
	      stringtok
             } toktype ;

toktype      mapflex_currenttoken;
char        *mapflex_currentstring;
long double  mapflex_currentlongreal;
int          mapflex_currentinteger;


#define YY_DECL void yylex (void)
%}

%%
\n.*                      { consumeLine(); /* printf("found: %s\n", currentLine->linebuf); */ }
\/\/.*\n                  { updatepos(FALSE); /* ignore comments.  */ }
[\-]?([0-9]+)             { updatepos(TRUE);
                            mapflex_currenttoken = integertok;
                            mapflex_currentinteger = atoi (yytext);
                            return; }
[\-]?([0-9]*)\.([0-9]*)   { updatepos(TRUE);
                            mapflex_currenttoken = longrealtok;
                            mapflex_currentlongreal = strtold (yytext, NULL);
                            return; }
[ \t]*                    { updatepos(FALSE); }
\"[^\"\n]*\"              { updatepos(TRUE);
			    mapflex_currenttoken = stringtok;
			    return;
                          }
\(                        { updatepos(TRUE); mapflex_currenttoken = lrbratok; return; }
\)                        { updatepos(TRUE); mapflex_currenttoken = rrbratok; return; }
\{                        { updatepos(TRUE); mapflex_currenttoken = lcbratok; return; }
\}                        { updatepos(TRUE); mapflex_currenttoken = rcbratok; return; }
Version                   { updatepos(TRUE); mapflex_currenttoken = versiontok; return; }
version                   { updatepos(TRUE); mapflex_currenttoken = versiontok; return; }
brushdef3                 { updatepos(TRUE); mapflex_currenttoken = brushdef3tok; return; }
brushDef3                 { updatepos(TRUE); mapflex_currenttoken = brushdef3tok; return; }
patchdef2                 { updatepos(TRUE); mapflex_currenttoken = patchdef2tok; return; }
patchDef2                 { updatepos(TRUE); mapflex_currenttoken = patchdef2tok; return; }
<<EOF>>                   { updatepos(FALSE); mapflex_currenttoken = eoftok; return; }

%%

/*
 *  consumeLine - reads a line into a buffer, it then pushes back the whole
 *                line except the initial \n.
 */

static void consumeLine (void)
{
  if (currentLine->linelen<yyleng) {
    currentLine->linebuf = (char *)realloc (currentLine->linebuf, yyleng);
    currentLine->linelen = yyleng;
  }
  strcpy(currentLine->linebuf, yytext+1);  /* copy all except the initial \n */
  lineno++;
  currentLine->actualline = lineno;
  currentLine->tokenpos=0;
  currentLine->nextpos=0;
  currentLine->column=0;
  yyless(1);                  /* push back all but the \n */
}

/*
 *  updatepos - updates the current token position.
 *              Should be used when a rule matches a token.
 */

static void updatepos (int remember)
{
  currentLine->nextpos = currentLine->tokenpos+yyleng;
  currentLine->toklen  = yyleng;
  if (currentLine->column == 0)
    currentLine->column = currentLine->tokenpos;
  if (remember)
    {
      if (mapflex_currentstring != NULL)
	free (mapflex_currentstring);
      mapflex_currentstring = strdup (yytext);
    }
}

/*
 *  skippos - skips over this token. This function should be called
 *            if we are not returning and thus not calling getToken.
 */

static void skippos (void)
{
  currentLine->tokenpos = currentLine->nextpos;
}

/*
 *  initLine - initializes a currentLine
 */

static void initLine (void)
{
  currentLine = (struct lineInfo *) malloc (sizeof (struct lineInfo));

  if (currentLine == NULL)
    perror("malloc");
  currentLine->linebuf    = NULL;
  currentLine->linelen    = 0;
  currentLine->tokenpos   = 0;
  currentLine->toklen     = 0;
  currentLine->nextpos    = 0;
  currentLine->column     = 0;
  currentLine->actualline = lineno;
}

/*
 *  resetpos - resets the position of the next token to the start of the line.
 */

static void resetpos (void)
{
  if (currentLine != NULL)
    currentLine->nextpos = 0;
}

/*
 *  mapflex_getToken - returns a new token.
 */

void mapflex_getToken (void)
{
  if (currentLine == NULL)
    initLine();
  currentLine->tokenpos = currentLine->nextpos;
  yylex();
  if (mapOptions_debugging ())
    printf ("seen %s\n", mapflex_currentstring);
}

void mapflex_error (const char *s)
{
  if (currentLine != NULL) {
    printf("%s:%d:%s\n", filename, currentLine->actualline, s);
    printf("%s\n", currentLine->linebuf);
# if 0
    printf("%*s%*s\n", currentLine->nextpos, " ", currentLine->toklen, "^");
# endif
  }
}

/*
 *  mapflex_getColumnNo - returns the column where the current
 *                        token starts.
 */

int mapflex_getColumnNo (void)
{
  if (currentLine != NULL)
    return currentLine->column;
  else
    return 0;
}

/*
 *  openSource - returns TRUE if file, s, can be opened and
 *               all tokens are taken from this file.
 */

int mapflex_openSource (char *s)
{
  FILE *f = fopen(s, "r");

  if (f == NULL)
    return FALSE;
  else {
    yy_delete_buffer(YY_CURRENT_BUFFER);
    yy_switch_to_buffer(yy_create_buffer(f, YY_BUF_SIZE));
    filename = strdup(s);
    lineno   =1;
    if (currentLine != NULL)
      currentLine->actualline = lineno;
    return TRUE;
  }
}

char *mapflex_getFileName (void)
{
  return filename;
}

/*
 *  closeSource - provided for semantic sugar
 */

void mapflex_closeSource (void)
{
}

/*
 *  mapflex_getLineNo - returns the current line number.
 */

int mapflex_getLineNo (void)
{
  if (currentLine != NULL)
    return currentLine->actualline;
  else
    return 0;
}

/*
 *  yywrap is called when end of file is seen. We push an eof token
 *         and tell the lexical analysis to stop.
 */

int yywrap (void)
{
  updatepos (FALSE); return 1;
}

void _M2_mapflex_init (void) {}
void _M2_mapflex_finish (void) {}
