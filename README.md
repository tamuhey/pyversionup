# Versionup cli for Python

- rewrite version name in `setup.cfg`
- (optional) commit and add version tag
- (optional) rewrite version name in specified files

## Install

```bash
$ pip install git+https://github.com/tamuhey/pyversionup
# specific version
$ pip install git+https://github.com/tamuhey/pyversionup@v0.0.2
```

## Usage

```bash
$ versionup v0.0.1
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