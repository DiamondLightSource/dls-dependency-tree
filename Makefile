# Specify defaults for testing
PREFIX=/scratch/tools
PYTHON=$(PREFIX)/bin/python2.6
INSTALL_DIR=$(PREFIX)/lib/python2.6/site-packages
SCRIPT_DIR=$(PREFIX)/bin
MODULEVER=0.0

# Override with any release info
-include Makefile.private

# uic files
PYUIC=$(PREFIX)/bin/pyuic4
UICS=$(patsubst %.ui, %_ui.py, $(wildcard dls_dependency_tree/*.ui))

# build the screens from .ui source
%_ui.py: %.ui
	$(PYUIC) -o $@ $<

# This is run when we type make
dist: setup.py $(wildcard dls_dependency_tree/*) $(UICS)
	MODULEVER=$(MODULEVER) $(PYTHON) setup.py bdist_egg
	touch dist
	$(MAKE) -C documentation

# Clean the module
clean:
	$(PYTHON) setup.py clean
	-rm -rf build dist *egg-info $(UICS) installed.files 
	-find -name '*.pyc' -exec rm {} \;
	$(MAKE) -C documentation clean	

# Install the built egg
install: dist
	$(PYTHON) setup.py easy_install -m \
		--record=installed.files \
		--install-dir=$(INSTALL_DIR) \
		--script-dir=$(SCRIPT_DIR) dist/*.egg
		
