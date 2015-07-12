DOCDIR   = documentation

all:
	cp README.rst $(DOCDIR)/source/_static
	cp License.txt $(DOCDIR)/source/_static
	$(MAKE) -C $(DOCDIR) latexpdf
	cp $(DOCDIR)/build/latex/*.pdf $(DOCDIR)/source/_static
	$(MAKE) -C $(DOCDIR) html

