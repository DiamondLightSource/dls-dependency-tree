import subprocess
import re
import shutil
import os.path
from typing import Tuple, Optional
from .constants import BUILDER_IOC_REGEX
try:
    from PyQt5.QtWidgets import QMessageBox
    qt_imported = True
except:
    qt_imported = False


def build_ioc(release_path: str, check_running_from_work: bool = False,
loading_box: bool = False) -> Optional[Tuple[str, str]]:
    if not re.match(BUILDER_IOC_REGEX, release_path):
        return ("", "Could not build IOC as not a valid builder RELEASE path")
    parts = release_path.split("/")
    builder_path = "/".join(parts[:6])
    ioc_name = parts[-1].rstrip("_RELEASE")
    if check_running_from_work:
        completed_process = subprocess.run([f"configure-ioc s {ioc_name}"],
                                        capture_output=True, shell=True)
        stdout = completed_process.stdout.decode()
        stderr = completed_process.stderr.decode()
        if stderr:
            return
        elif "/dls_sw/work/" in stdout and qt_imported:
            response = QMessageBox.question(
                None,
                "Build IOC",
                "WARNING: Are you sure you want to rebuild?"
                f" The IOC is running from {stdout.split(' ')[-1]}",
                QMessageBox.Yes,
                QMessageBox.No,
            )

            if response == QMessageBox.No:
                return
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
        make -C etc/makeIocs IOCS={ioc_name} && \
        make -C iocs/{ioc_name};
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
