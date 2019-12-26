import configparser
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Iterable,
    Literal,
    Mapping,
    NamedTuple,
    Optional,
)

import toml

__version__ = "0.0.3"


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
PYPROJECT = "pyproject.toml"
VERSIONUP = "versionup"


@dataclass
class Config(NamedTuple):
    config: Mapping
    type_: Literal["setup", "poetry"]

    @property
    def version(self) -> str:
        if self.type_ == "setup":
            return self.config["metadata"]["version"]
        if self.type_ == "poetry":
            return self.config["tool"]["poetry"]["version"]
        raise ValueError()

    @version.setter
    def version(self, version: str):
        if self.type_ == "setup":
            self.config["metadata"]["version"] = version
        if self.type_ == "poetry":
            self.config["tool"]["poetry"]["version"] = version

    @property
    def versionup_config(self) -> Optional[Mapping]:
        return self.config.get("versionup", None)


def get_config() -> Config:
    if Path(SETUP_CFG).exists():
        config = configparser.ConfigParser()
        config.read(SETUP_CFG)
        return Config(config, "setup")
    if Path(PYPROJECT).exists():
        return Config(toml.load(PYPROJECT), "poetry")
    raise ValueError()


def main():
    new_version = sys.argv[1]
    config = get_config()
    old_version = config.version

    vcfg = config.versionup_config
    if vcfg:
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
