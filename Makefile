DOCDIR = docs

all:
	cp README.rst LICENSE.rst $(DOCDIR)/source
	rm -rf $(DOCDIR)/build
	$(MAKE) -C $(DOCDIR) latexpdf
	cp $(DOCDIR)/build/latex/*.pdf $(DOCDIR)/source/_static
	$(MAKE) -C $(DOCDIR) html
	git add -A
	git commit -a -m "rebuilt docs"

