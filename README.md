# `metadsl`

[![Documentation Status](https://readthedocs.org/projects/metadsl/badge/?version=latest)](https://metadsl.readthedocs.io/en/latest/?badge=latest)

A framework for creating domain specific language libraries in Python.


## Guiding Principles

The goal here is to share as much optimization and representation logic as possible, so that the world users
exist in can be extended more easily without having to cause them to change their code.

For example, if someone comes up with a new way of executing linear algebra or wants to try out a new way of optimizing
expressions, they should be able to write those things in a pluggable manner, so that users can try them out with minimal
effort. 

This means we have to explicitly expose the protocols of the different levels to foster distributed collaboration and reuse. 

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
pytest --cov
# open coverage file
open htmlcov/index.html
```

You can also test that the documentation notebooks run correctly, but this
[must be run separately from the code coverage](https://github.com/computationalmodelling/nbval/issues/116):

```bash
pytest docs/*.ipynb --nbval
````


### Docs

```bash
sphinx-autobuild docs docs/_build/html/
```
