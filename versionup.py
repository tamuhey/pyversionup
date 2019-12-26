import configparser
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing_extensions import Literal
from typing import (
    Any,
    Iterable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Union,
    cast,
)

import toml

__version__ = "v0.0.4.dev0"


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

FNAME = {"setup": SETUP_CFG, "poetry": PYPROJECT}


@dataclass
class Config:
    config: Mapping
    type_: Literal["setup", "poetry"]

    def save(self):
        if self.type_ == "setup":
            with open(SETUP_CFG, "w") as f:
                cast(configparser.ConfigParser, self.config).write(f)
        if self.type_ == "poetry":
            with open(PYPROJECT, "w") as f:
                toml.dump(self.config, PYPROJECT)

    @property
    def fname(self) -> str:
        return FNAME[self.type_]

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

    @property
    def target_files(self) -> List[str]:
        config = self.versionup_config
        if config:
            files: Union[str, List[str], None] = config.get("files")
            if isinstance(files, str):
                files = list(filter(lambda x: x != "", files.split("\n")))
            if files:
                return files
        return []

    @property
    def commit(self) -> bool:
        return self.vcfg_attr("commit")

    @property
    def tag(self) -> bool:
        return self.vcfg_attr("tag")

    def vcfg_attr(self, key: str, default=False) -> Any:
        vcfg = self.versionup_config
        return self.check_bool(vcfg.get(key, default), default=default)

    def check_bool(self, val: Union[str, bool], default=False) -> bool:
        if isinstance(val, bool):
            return val
        if val.lower() == "true":
            return True
        return default


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
    config.version = new_version

    vcfg = config.versionup_config
    if vcfg:
        rewrite_version(config.target_files, old_version, new_version)
        if config.commit:
            add([config.fname] + config.target_files)
            commit(old_version, new_version)

            if config.tag:
                tag(new_version)


if __name__ == "__main__":
    main()
