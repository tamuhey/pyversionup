# Versionup cli for Python

- rewrite version name in `setup.cfg`
- (optional) commit and add version tag
- (optional) rewrite version name in specified files

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

Write config in `setup.cfg`.
Example:

```
[versionup]
files = 
  src/VERSION.py
tag = True
commit = True
```
