import subprocess
import sys

from dls_dependency_tree import __version__


def test_cli_version():
    cmd = [sys.executable, "-m", "dls_dependency_tree", "--version"]
    assert subprocess.check_output(cmd).decode().strip() == __version__
