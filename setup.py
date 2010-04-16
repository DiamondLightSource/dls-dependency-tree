from setuptools import setup

# these lines allow the version to be specified in Makefile.private
import os
version = os.environ.get("MODULEVER", "0.0")

setup(
    # name of the module
    name = "dls_dependency_tree",
    # version: over-ridden by the release script
    version = version,
    packages = ["dls_dependency_tree"],
    # define console_scripts to be 
    entry_points = {'console_scripts': \
                    ['dls-dependency-checker.py = dls_dependency_tree.dependency_checker:dependency_checker']},
#    include_package_data = True,
    zip_safe = False
    )
