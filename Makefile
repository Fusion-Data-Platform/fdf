DOCDIR = docs

all:
	cp *.rst $(DOCDIR)/source
	$(MAKE) -C $(DOCDIR) latexpdf
	cp $(DOCDIR)/build/latex/*.pdf $(DOCDIR)/source/_static
	$(MAKE) -C $(DOCDIR) html

