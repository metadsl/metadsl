# `metadsl`

[![Documentation Status](https://readthedocs.org/projects/metadsl/badge/?version=latest)](https://metadsl.readthedocs.io/en/latest/?badge=latest)

A framework for creating domain specific language libraries in Python.

The initial use case is in scientific computing, where:

1. You want to use the the APIs you know and love (ex. NumPy).
2. But you want it to execute in a new way (ex. on a GPU or distributed accross machines).
3. And you want to optimize a chain of operations before executing (ex. `(x * y)[0]` -> `x[0] * y[0]` / [Mathematics of Arrays](https://paperpile.com/app/p/5de098dd-606d-0124-a25d-db5309f99394)).


## Guiding Principles

The goal here is to share as much optimization and representation logic as possible, so that the world users
exist in can be extended more easily without having to cause them to change their code.

For example, if someone comes up with a new way of executing linear algebra or wants to try out a new way of optimizing
expressions, they should be able to write those things in a pluggable manner, so that users can try them out with minimal
effort. 

This means we have to explicitly expose the protocols of the different levels to foster distributed collaboration and reuse. 

## [Roadmap](./ROADMAP.md)

## Development

Either use repo2docker:

```bash
repo2docker -E .
```


Or get started with Conda/flit:

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
