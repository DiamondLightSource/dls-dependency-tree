#!/bin/env python2.4
# dependency_tree of a setup.py file for any dls module
from setuptools import setup, find_packages, Extension

# this line allows the version to be specified in the release script
try:
    version = version
except:
    version = "0.0"

setup(
    # install_requires allows you to import a specific version of a module in your scripts 
    install_requires = ['dls.environment==1.0'],
    # setup_requires lets us use the site specific settings for installing scripts
    setup_requires = ["dls.environment==1.0"],
    # name of the module
    name = "dls_dependency_tree",
    # version: over-ridden by the release script
    version = version,
    packages = ["dls_dependency_tree"],
    package_dir = { 'dls_dependency_tree': 'src'},
    # define console_scripts to be 
    entry_points = {'console_scripts': \
                    ['dls-dependency-checker.py = dls_dependency_tree.dependency_checker:dependency_checker', \
                     'dls-tree-paths.py = dls_dependency_tree.dependency_tree:cl_dependency_tree']},
    include_package_data = True,
    zip_safe = False
    )
