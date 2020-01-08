from typing import Optional
from versionup import get_user_option
import toml
import pytest
import sys
import random
import subprocess
from pathlib import Path
import shutil


BASEDIR = Path(__file__).parent
CONFFILE = "pyproject.toml"


@pytest.fixture(params=[True, False])
def _tag(request):
    return request.param


@pytest.fixture(params=["foo/", ""])
def tag_prefix(request):
    return request.param


@pytest.fixture(params=[True, False])
def _commit(request):
    return request.param


@pytest.fixture
def setup_conffile(_tag, tag_prefix, _commit):
    cfg = toml.load(str(BASEDIR / CONFFILE))
    cfg["versionup"]["tag"] = _tag
    cfg["versionup"]["tag_prefix"] = tag_prefix
    cfg["versionup"]["commit"] = _commit
    with (BASEDIR / CONFFILE).open("w") as f:
        toml.dump(cfg, f)


@pytest.fixture
def setup(setup_conffile):
    subprocess.run(["git", "init"], cwd=str(BASEDIR))
    subprocess.run(["git", "commit", "-m", '"foo"', "--allow-empty"], cwd=str(BASEDIR))
    yield
    shutil.rmtree(str(BASEDIR / ".git"))


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


def test_versionup(setup, tag, tag_prefix, commit, cli_optional_args):
    new_version = str(random.randint(0, 1000000))
    result = subprocess.run(
        [sys.executable, str(BASEDIR / "../../versionup.py"), new_version]
        + cli_optional_args,
        cwd=str(BASEDIR),
    )
    assert result.returncode == 0
    assert new_version in (BASEDIR / "foo.txt").open().read()
    assert new_version in (BASEDIR / "pyproject.toml").open().read()

    if commit:
        result = subprocess.run(
            ["git", "rev-list", "--all", "--count"],
            cwd=str(BASEDIR),
            capture_output=True,
        )
        assert result.stdout.decode().strip() == "2"

    if tag and commit:
        result = subprocess.run(
            ["git", "describe", "--tags"], cwd=str(BASEDIR), capture_output=True,
        )
        assert result.stdout.decode().strip() == tag_prefix + new_version

