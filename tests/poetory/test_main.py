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
def tag(request):
    return request.param


@pytest.fixture(params=["foo/", ""])
def tag_prefix(request):
    return request.param


@pytest.fixture(params=[True, False])
def commit(request):
    return request.param


@pytest.fixture
def setup_conffile(tag, tag_prefix, commit):
    cfg = toml.load(str(BASEDIR / CONFFILE))
    cfg["versionup"]["tag"] = tag
    cfg["versionup"]["tag_prefix"] = tag_prefix
    cfg["versionup"]["commit"] = commit
    with (BASEDIR / CONFFILE).open("w") as f:
        toml.dump(cfg, f)


@pytest.fixture
def setup(setup_conffile):
    subprocess.run(["git", "init"], cwd=str(BASEDIR))
    subprocess.run(["git", "commit", "-m", '"foo"', "--allow-empty"], cwd=str(BASEDIR))
    yield
    shutil.rmtree(str(BASEDIR / ".git"))


def test_versionup(setup, tag, tag_prefix, commit):
    new_version = str(random.randint(0, 1000000))
    result = subprocess.run(
        [sys.executable, str(BASEDIR / "../../versionup.py"), new_version],
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

