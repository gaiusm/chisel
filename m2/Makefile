PG = ${HOME}/GM2/graft-svn-trunc/build-svn-trunc/gcc/gm2/pg

test: all
	./map2bsp -d examples/map/test.map

all: parser.o mapflex.o vector3.o mapDebug.o nameKey.o mapError.o mapOptions.o bsp.o map2bsp.o
	gm2 -fm2-g -g map2bsp.mod -o map2bsp

%.o: %.mod
	gm2 -fm2-g -g -c $<

%.o: %.c
	gcc -g -c $<

parser.mod:  parser.bnf
	$(PG) -l $< > $@

mapflex.c: map.flex
	flex -t $< > $@

clean: force
	$(RM) *.o parser.mod mapflex.c *~ *.cpp *.s

force:
