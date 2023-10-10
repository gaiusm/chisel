SUFFIXES = .c .mod .def .o .obj .lo .a .m .mxm

SHELL=/bin/bash

prefix= @prefix@
datarootdir= @datarootdir@
srcdir= @srcdir@
mandir= @mandir@
exec_prefix=@exec_prefix@
bindir= @bindir@
INSTALL_PROGRAM = install

PYTHON_VERSION=$(strip $(shell python3 -V 2>&1 | cut -b8- | cut -f1-2 -d'.'))

python_PYTHON3 = python/pen2map.py python/txt2pen.py python/chvec.py python/student/chcuboid.py python/poly.py

help:  force
	@echo "knows about:  all, clean, install

SUBDIRS = random

install: force
	cp $(srcdir)/python/poly.py .
	cp $(srcdir)/python/chvec.py .
	cp $(srcdir)/python/student/chcuboid.py .
	cp $(srcdir)/python/pen2map.py .
	cp $(srcdir)/python/txt2pen.py .
	cp $(srcdir)/python/txt2txt.py .
	PYTHONPATH=.:$(srcdir)/python python3 $(srcdir)/chiselsetup.py build
	$(INSTALL_PROGRAM) -m 755 $(srcdir)/shell/txt2map $(DESTDIR)/usr/bin
	$(INSTALL_PROGRAM) -m 755 shell/pen2map $(DESTDIR)/usr/bin
	$(INSTALL_PROGRAM) -m 755 shell/txt2pen $(DESTDIR)/usr/bin
	$(INSTALL_PROGRAM) -m 755 -d $(DESTDIR)/usr/lib/python$(PYTHON_VERSION)/site-packages/chisel
	$(INSTALL_PROGRAM) -m 644 poly.py $(DESTDIR)/usr/lib/python$(PYTHON_VERSION)/site-packages/chisel
	$(INSTALL_PROGRAM) -m 644 chvec.py $(DESTDIR)/usr/lib/python$(PYTHON_VERSION)/site-packages/chisel
	$(INSTALL_PROGRAM) -m 644 chcuboid.py $(DESTDIR)/usr/lib/python$(PYTHON_VERSION)/site-packages/chisel
	$(INSTALL_PROGRAM) -m 644 pen2map.py $(DESTDIR)/usr/lib/python$(PYTHON_VERSION)/site-packages/chisel
	$(INSTALL_PROGRAM) -m 644 txt2pen.py $(DESTDIR)/usr/lib/python$(PYTHON_VERSION)/site-packages/chisel
	$(INSTALL_PROGRAM) -m 644 txt2txt.py $(DESTDIR)/usr/lib/python$(PYTHON_VERSION)/site-packages/chisel

install-data-hook: force
	rm -f $(DESTDIR)/usr/lib/python$(PYTHON_VERSION)/dist-packages/chcuboid.py

install-data-local: force
	$(INSTALL_PROGRAM) -m 755 shell/txt2pen $(DESTDIR)/usr/bin
	$(INSTALL_PROGRAM) -m 755 shell/pen2map $(DESTDIR)/usr/bin
	$(INSTALL_PROGRAM) -m 755 $(srcdir)/shell/txt2map $(DESTDIR)/usr/bin

regression: force
	for i in $(srcdir)/maps/*txt ; do \
            echo "building $$i" ; \
            txt2map $$i ; \
        done

documentation: chisel.pdf

chisel.pdf: chisel.ps
	gs -q -dBATCH -dNOPAUSE -sDEVICE=pdfwrite -sOutputFile=$@ $<

chisel.ps: chisel.dvi
	dvips -o $@ $<

chisel.dvi: $(srcdir)/doc/chisel.texi
	texi2dvi -I $(srcdir)/ $(srcdir)/doc/chisel.texi

release: force
	echo chisel-`sed -e '/version_string/!d' \
          -e 's/[^0-9.]*\([0-9.]*\).*/\1/' -e q $(srcdir)/version.c` > .fname
	-rm -rf `cat .fname`
	mkdir `cat .fname`
	dst=`cat .fname`; for f in $(DISTFILES); do \
           cp -rp $(srcdir)/$$f $$dst/$$f ; \
        done
	tar --gzip -chf `cat .fname`.tar.gz `cat .fname`
	-rm -rf `cat .fname` .fname

clear: force
	$(RM) *.png *.ms *.cpp

force:
