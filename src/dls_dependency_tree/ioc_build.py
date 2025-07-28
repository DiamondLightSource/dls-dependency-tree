import os
import re
import shutil


def build_ioc(release_path: str):
    if not re.match(r"^\/dls_sw\/work\/R3\.14\.12\.7\/support\/BL[0-9]{2}[BIJK]-BUILDER"
                    r"\/etc\/makeIocs\/BL[0-9]{2}[BIJK]-[A-Z0-9]{2}-IOC-[0-9]{2}_RELEASE$",
                    release_path):
        print("Could not build IOC as not a valid builder RELEASE path")
        return
    parts = release_path.split("/")
    builder_path = "/".join(parts[:6])
    ioc_name = parts[-1].rstrip("_RELEASE")
    print(builder_path, ioc_name)

    if os.path.isdir(f"{builder_path}/iocs/{ioc_name}"):
        shutil.rmtree(f"{builder_path}/iocs/{ioc_name}", ignore_errors=True)

    make_command = f"""
        cd {builder_path} && \
        touch etc/makeIocs/{ioc_name}.xml && \
        make -C etc/makeIocs IOCS={ioc_name} && \
        make -C iocs/{ioc_name};
    """
    os.system(make_command)

