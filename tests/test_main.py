from os import write
from typing import Mapping, Optional
import toml
from configparser import ConfigParser
from versionup import CONF, get_user_option
import configparser
import pytest
import sys
import random
import subprocess
from pathlib import Path
import shutil


BASEDIR = Path(__file__).parent
CONFFILE = "setup.cfg"
CONF_TYPES = {
    "setup.cfg": ("setup.cfg", BASEDIR / "setup_cfg"),
    "poetry": ("pyproject.toml", BASEDIR / "poetry"),
}


@pytest.fixture(params=list(CONF_TYPES))
def conftype(request):
    return request.param


@pytest.fixture
def cwd(conftype) -> Path:
    return CONF_TYPES[conftype][1]


@pytest.fixture
def conffile(conftype) -> Path:
    return CONF_TYPES[conftype][0]


@pytest.fixture(params=[True, False])
def _tag(request):
    return request.param


@pytest.fixture(params=["foo/", ""])
def tag_prefix(request):
    return request.param


@pytest.fixture(params=[True, False])
def _commit(request):
    return request.param


def load_cfg(conftype: str, fpath: str) -> CONF:
    if conftype == "setup.cfg":
        cfg = configparser.ConfigParser()
        cfg.read(fpath)
    elif conftype == "poetry":
        cfg = toml.load(fpath)
    else:
        raise ValueError
    return cfg


def write_cfg(cfg: CONF, conftype: str, fpath: str):
    with open(str(fpath), "w") as f:
        if conftype == "setup.cfg":
            cfg.write(f)
        elif conftype == "poetry":
            toml.dump(cfg, f)
        else:
            raise ValueError


def boollike(conftype: str, b: bool):
    if conftype == "setup.cfg":
        return str(b).lower()
    return b


@pytest.fixture
def setup_conffile(_tag, tag_prefix, _commit, conftype, cwd, conffile):
    confpath = str(cwd / conffile)
    cfg = load_cfg(conftype, confpath)
    cfg["versionup"]["tag"] = boollike(conftype, _tag)
    cfg["versionup"]["tag_prefix"] = tag_prefix
    cfg["versionup"]["commit"] = boollike(conftype, _commit)
    write_cfg(cfg, conftype, confpath)


@pytest.fixture
def setup(setup_conffile, cwd):
    subprocess.run(["git", "init"], cwd=str(cwd))
    subprocess.run(["git", "commit", "-m", '"foo"', "--allow-empty"], cwd=str(cwd))
    yield
    shutil.rmtree(str(cwd / ".git"))


@pytest.fixture(params=[True, False, None])
def cli_flag_commit(request):
    return request.param


@pytest.fixture(params=[True, False, None])
def cli_flag_tag(request):
    return request.param


def get_cli_optional_flag_str(name: str, value: Optional[bool]) -> str:
    if value is None:
        return ""
    if value:
        return f"--{name}"
    return f"--no{name}"


@pytest.fixture
def cli_optional_args(cli_flag_commit, cli_flag_tag):
    return list(
        filter(
            lambda x: x != "",
            (
                get_cli_optional_flag_str(k, v)
                for k, v in [("commit", cli_flag_commit), ("tag", cli_flag_tag)]
            ),
        )
    )


@pytest.fixture
def commit(_commit, cli_flag_commit):
    return get_user_option(_commit, cli_flag_commit)


@pytest.fixture
def tag(_tag, cli_flag_tag):
    return get_user_option(_tag, cli_flag_tag)


def test_versionup(setup, tag, tag_prefix, commit, cli_optional_args, cwd, conffile):
    new_version = str(random.randint(0, 1000000))
    result = subprocess.run(
        [sys.executable, str(cwd / "../../versionup.py"), new_version]
        + cli_optional_args,
        cwd=str(cwd),
    )
    assert result.returncode == 0
    assert new_version in (cwd / "foo.txt").open().read()
    assert new_version in (cwd / conffile).open().read()

    if commit:
        result = subprocess.run(
            ["git", "rev-list", "--all", "--count"], cwd=str(cwd), capture_output=True,
        )
        assert result.stdout.decode().strip() == "2"

    if tag and commit:
        result = subprocess.run(
            ["git", "describe", "--tags"], cwd=str(cwd), capture_output=True,
        )
        assert result.stdout.decode().strip() == tag_prefix + new_version

