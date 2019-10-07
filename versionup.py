import sys
import configparser
from pathlib import Path
from typing import Iterable
import subprocess

__version__ = "v0.0.2"


def versionup(p: Path, old, new):
    with p.open() as f:
        text = f.read()
    with p.open("w") as f:
        f.write(text.replace(old, new))


def rewrite_version(filenames: Iterable[str], old, new):
    for fname in filenames:
        if fname:
            p = Path(fname)
            versionup(p, old, new)
            print(f"Update: {str(p)}")


def call(cmd):
    proc = subprocess.run(cmd, capture_output=True)
    print(proc.stdout.decode())
    print(proc.stderr.decode())


def add(files: Iterable[str]):
    cmd = ["git", "add"] + list(files)
    call(cmd)


def commit(old_version, new_version):
    cmd = [
        "git",
        "commit",
        "--allow-empty",
        "-m",
        f'"versionup: {old_version} -> {new_version}"',
    ]
    call(cmd)


def tag(tagname):
    cmd = ["git", "tag", tagname]
    call(cmd)


SETUP_CFG = "setup.cfg"
VERSIONUP = "versionup"


def main():
    config = configparser.ConfigParser()
    config.read(SETUP_CFG)
    old_version = config["metadata"]["version"]
    new_version = sys.argv[1]
    config["metadata"]["version"] = new_version
    with open(SETUP_CFG, "w") as f:
        config.write(f)
    print(f"Update: {SETUP_CFG}")

    if VERSIONUP in config:
        vcfg = config[VERSIONUP]
        files = vcfg.get("files")
        if files:
            files = list(filter(lambda x: x != "", files.split("\n")))
            rewrite_version(files, old_version, new_version)
        else:
            files = []
        if vcfg.get("commit") == "True":
            add([SETUP_CFG] + files)
            commit(old_version, new_version)

            if vcfg.get("tag") == "True":
                tag(new_version)


if __name__ == "__main__":
    main()
