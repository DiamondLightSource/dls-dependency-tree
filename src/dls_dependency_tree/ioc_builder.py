import subprocess
import re
import shutil
import os.path
from typing import Tuple

def build_ioc(release_path: str) -> Tuple[str, str]:
    if not re.match(r"^\/dls_sw\/work\/R3\.14\.12\.7\/support\/BL[0-9]{2}[BIJK]-BUILDER"
                    r"\/etc\/makeIocs\/BL[0-9]{2}[BIJK]-[A-Z0-9]{2}-IOC-[0-9]{2}_RELEASE$",
                    release_path):
        print("Could not build IOC as not a valid builder RELEASE path")
        return
    parts = release_path.split("/")
    builder_path = "/".join(parts[:6])
    ioc_name = parts[-1].rstrip("_RELEASE")

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
    stdout, stderr = completed_process.stdout.decode(), completed_process.stderr.decode()
    return stdout, stderr
