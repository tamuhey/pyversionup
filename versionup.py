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

__version__ = "0.0.6"


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
POETRY = "poetry"
SETUP = "setup"

FNAME = {SETUP: SETUP_CFG, POETRY: PYPROJECT}


@dataclass
class Config:
    config: Mapping
    type_: Literal["setup", "poetry"]

    def save(self):
        if self.type_ == SETUP:
            with open(SETUP_CFG, "w") as f:
                cast(configparser.ConfigParser, self.config).write(f)
        if self.type_ == POETRY:
            with open(PYPROJECT, "w") as f:
                toml.dump(self.config, f)

    @property
    def fname(self) -> str:
        return FNAME[self.type_]

    @property
    def version(self) -> str:
        if self.type_ == SETUP:
            return self.config["metadata"]["version"]
        if self.type_ == POETRY:
            return self.config["tool"][POETRY]["version"]
        raise ValueError()

    @version.setter
    def version(self, version: str):
        if self.type_ == SETUP:
            self.config["metadata"]["version"] = version
            return
        if self.type_ == POETRY:
            self.config["tool"][POETRY]["version"] = version
            return
        raise ValueError()

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
        return Config(config, SETUP)
    if Path(PYPROJECT).exists():
        return Config(toml.load(PYPROJECT), POETRY)
    raise ValueError()


def main():
    new_version = sys.argv[1]
    config = get_config()
    print("Load type: ", config.type_)
    old_version = config.version
    config.version = new_version
    config.save()

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
