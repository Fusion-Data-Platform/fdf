DOCDIR   = docs

all:
	cp README.rst $(DOCDIR)/source/_static
	cp LICENSE.txt $(DOCDIR)/source/_static
	$(MAKE) -C $(DOCDIR) latexpdf
	cp $(DOCDIR)/build/latex/*.pdf $(DOCDIR)/source/_static
	$(MAKE) -C $(DOCDIR) html

