# Specify where we should build for testing
PREFIX=/scratch/tools
INSTALL_DIR=$(PREFIX)/lib/python2.6/site-packages
SCRIPT_DIR=$(PREFIX)/bin
PYTHON=$(PREFIX)/bin/dls-python2.6
PYUIC=$(PREFIX)/bin/pyuic2.6

# uic files
UICS=$(patsubst %.ui, %_ui.py, $(wildcard dls_dependency_tree/*.ui))

# build the screens from .ui source
%_ui.py: %.ui
	$(PYUIC) -o $@ -p0 $<$

# This is run when we type make
dist: setup.py $(wildcard dependency_tree/*) $(UICS)
	$(PYTHON) setup.py bdist_egg
	touch dist

# Clean the module
clean:
	$(PYTHON) setup.py clean
	-rm -rf build dist *egg-info $(UICS) installed.files 
	-find -name '*.pyc' -exec rm {} \;

# Install the built egg
install: dist
	$(PYTHON) setup.py easy_install -m \
		--record=installed.files \
		--install-dir=$(INSTALL_DIR) \
		--script-dir=$(SCRIPT_DIR) dist/*.egg
		
