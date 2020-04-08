import subprocess
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Mapping, Optional, Union

import fire
import toml
from typing_extensions import Literal


__version__ = "0.1.3.dev11"
DEFAULT_MSG = "[versionup] $old_version -> $new_version"


def versionup(p: Path, old, new):
    text = p.read_text()
    p.write_text(text.replace(old, new))


def rewrite_version(filenames: Iterable[str], old, new):
    for fname in filenames:
        versionup(Path(fname), old, new)
        print(f"Update: {fname}")


def call(cmd):
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(proc.stdout.decode())
    print(proc.stderr.decode())
    proc.check_returncode()


def add(files: Iterable[str]):
    cmd = ["git", "add"] + list(files)
    call(cmd)


def create_message(old_version: str, new_version: str, message: str) -> str:
    replace = {r"\$old_version\b": old_version, r"\$new_version\b": new_version}
    for a, b in replace.items():
        message = re.sub(a, b, message)
    return message


def git_commit(old_version: str, new_version: str, message: str):
    cmd = [
        "git",
        "commit",
        "--allow-empty",
        "-m",
        create_message(old_version, new_version, message),
    ]
    call(cmd)


def git_tag(tagname):
    cmd = ["git", "tag", tagname]
    call(cmd)


VERSIONUP = "versionup"
POETRY = "poetry"
PYPROJECT_TOML = "pyproject.toml"


@dataclass
class Config:
    config: Mapping

    def save(self):
        with open(PYPROJECT_TOML, "w") as f:
            toml.dump(self.config, f)

    @classmethod
    def load(cls) -> "Config":
        if Path(PYPROJECT_TOML).exists():
            return Config(toml.load(PYPROJECT_TOML))
        raise ValueError(f"{PYPROJECT_TOML} not found")

    @property
    def version(self) -> str:
        return self.config["tool"][POETRY]["version"]

    @version.setter
    def version(self, version: str):
        self.config["tool"][POETRY]["version"] = version

    @property
    def versionup_config(self) -> Optional[Mapping]:
        if "tool" in self.config:
            return self.config["tool"].get("versionup", None)
        return None

    @property
    def target_files(self) -> List[str]:
        config = self.versionup_config
        files = [PYPROJECT_TOML]
        if config:
            files: List[str] = files + config.get("files", [])
        return files

    @property
    def commit(self) -> bool:
        return self.vcfg_attr("commit")

    @property
    def tag(self) -> bool:
        return self.vcfg_attr("tag")

    @property
    def tag_prefix(self) -> str:
        return self.versionup_config.get("tag_prefix", "")

    @property
    def message(self) -> str:
        return self.versionup_config.get("message", DEFAULT_MSG)

    def vcfg_attr(self, key: str, default=False) -> Any:
        vcfg = self.versionup_config
        return self.check_bool(vcfg.get(key, default), default=default)

    def check_bool(self, val: Union[str, bool], default=False) -> bool:
        if isinstance(val, bool):
            return val
        if val.lower() == "true":
            return True
        return default


def main(
    new_version: str = "",
    commit: Optional[bool] = None,
    tag: Optional[bool] = None,
    message: str = "",
):
    new_version = str(new_version)
    config = Config.load()
    print("Current version: ", config.version)
    print("New version: ", new_version)
    if not new_version:
        return
    old_version = config.version
    config.version = new_version
    config.save()

    vcfg = config.versionup_config
    if vcfg:
        rewrite_version(config.target_files, old_version, new_version)
        if commit or config.commit:
            add(config.target_files)
            git_commit(old_version, new_version, message or config.message)

            if tag or config.tag:
                git_tag(config.tag_prefix + new_version)


def cli():
    fire.Fire(main)


if __name__ == "__main__":
    cli()
