# Versionup cli for Python

- rewrite version name in `pyproject.toml`
- (optional) commit and add a version tag
- (optional) rewrite version string in specified files

## Install

```bash
$ pip install pyversionup
```

- from master

```bash
$ pip install -U git+https://github.com/tamuhey/pyversionup
```

## Usage

```bash
$ versionup 0.0.1
```

## Config

Write config in `pyproject.toml`.
Example:

```
[tool.versionup]
files = [ "my_pkg/VERSION.py",]
commit = true
```
