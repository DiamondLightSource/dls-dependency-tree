from setuptools import setup

# this line allows the version to be specified in the release script
globals().setdefault('version', '0.0')

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
