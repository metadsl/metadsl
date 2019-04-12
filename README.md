# `metadsl`

[![Documentation Status](https://readthedocs.org/projects/metadsl/badge/?version=latest)](https://metadsl.readthedocs.io/en/latest/?badge=latest)


A framework for creating domain specific language libraries in Python.

The end goal is for libraries like NumPy, Dask, Numba, and AutoGraph to be able to share
optimizations and representations, as much as possible.

The MVP is a lazy version of the NumPy API that can execute normally, but creates
an intermediate form that expresses the operations to perform, before performing them.

## Why?

1. You want to map Python to some other execution context.
2. But you want users to be able to use their existing APIs they know and love.
3. Also you want to build up some larger chunk of computation to dispatch, instead of executing every function.

This project explores how to do that, in a way where we can share work and multiple DSLs can easily talk to one another.


## Roadmap

- [ ] Get NP select example working, with codegen
    - [ ] Figure out Pure/compat type story. 
    - [ ] Copy over similar replacement based system so we can reuse existing uarray work
    - [ ] Copy over previous uarray work, update to work with new functions

## Development

Either use repo2docker:

```bash
repo2docker -E .
```


Or get started with conda:

```bash
conda create -n metadsl jupyterlab
conda activate metadsl
pip install flit
flit install --symlink
```

### Tests

This runs mypy and tests, and reports coverage.
```bash
pytest
# open coverage file
open htmlcov/index.html
```


### Docs

```bash
cd docs/
# build
make html
# serve
python -m http.server -d _build/html/
```
