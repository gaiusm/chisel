
AM_DEFAULT_SOURCE_EXT = .mod

bin_PROGRAMS = rndmap

rndmap_SOURCES = AdvMap.mod Chance.mod Geometry.mod MakeBoxes.mod \
                 MapOptions.mod RoomMap.mod StoreCoords.mod WriteMap.mod \
                 BoxMap.mod GetOpt.mod Map.mod Options.mod getopt.c

rndmap_LINK = gm2 -g -I$(srcdir) $(srcdir)/Map.mod -o $@

.mod.o:
	gm2 -I$(srcdir) -fm2-g -g -c $<
