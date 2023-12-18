import subprocess
import re
import shutil
import os.path
from typing import Tuple, Optional
from .constants import BUILDER_IOC_REGEX, IOC_TMPDIR
try:
    from PyQt5.QtWidgets import QMessageBox
    qt_imported = True
except:
    qt_imported = False


def build_ioc(release_path: str,
              loading_box: bool = False) -> Optional[Tuple[str, str]]:
    if not re.match(BUILDER_IOC_REGEX, release_path):
        return ("", "Could not build IOC as not a valid builder RELEASE path")
    parts = release_path.split("/")
    builder_path = "/".join(parts[:6])
    ioc_name = parts[-1].rstrip("_RELEASE")
    x = None
    if loading_box and qt_imported:
        x = QMessageBox()
        x.setText("Building IOC, please wait")
        x.setWindowTitle("Building...")
        x.show()
    if os.path.isdir(f"{builder_path}/iocs/{ioc_name}"):
        shutil.rmtree(f"{builder_path}/iocs/{ioc_name}", ignore_errors=True)

    make_command = f"""
        cd {builder_path} && \
        touch etc/makeIocs/{ioc_name}.xml && \
        mkdir -p {IOC_TMPDIR}/ && \
        rm -rf {IOC_TMPDIR}/{ioc_name} && \
        dls-xml-iocbuilder.py etc/makeIocs/{ioc_name}.xml -o {IOC_TMPDIR} && \
        make -C {IOC_TMPDIR}/{ioc_name};
    """

    # if we use subprocess we can capture the stdout and stderr and print to dialog box
    completed_process = subprocess.run(make_command, capture_output=True, shell=True)
    stdout, stderr = (
        completed_process.stdout.decode(),
        completed_process.stderr.decode(),
    )
    if x is not None:
        x.close()
    return stdout, stderr
