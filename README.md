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

## Notes on GS

Julia connection

History, had E2E version working on writing NP code, rew

Chance for Python to leepfrog what julia has done, using ideas from APL to compile array expression optmimially.

Fracturing in numerical community.

Once there was NP, then pandas came and sat on top of it.

Now there are a lot of things, all with different underlying representations

Easy access to linear algebra operations.
Regression, generelizaed linear model.
May want to use unstructured data and neural networks.

Pandas -> Sparse vector or one hot vecotr? no fly.
-> If I have out of memory? Well then we go to dask and pyspark.

Tremendous amount of inconsistancy.

At GS: Grammer of for univeriant time series, expressive. Anyone could understand anyone elses code.
Functional programming paradigm for constructing objects on a DAG, side effect free way to describe,
-> Ability to understand code that other people wrote.

Functional, side effect, let you get down to low level, but allow high level descriptions, allow handling sparseness, distributed nature.

Perhaps I should write another DSL, did this in Julia,

Haskell takes you away from the python community.

---

Telling a story

Highlight shortcomings, allow uniform API.

Want consistant API. There isn't a good tool to build it, need tool build

Remove MoA

just a backend uarray

How to get

Add numba

add Graph

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
flit -f core.pyproject.toml install --symlink
flit -f visualize.pyproject.toml install --symlink

# optional
jupyter labextension install @jupyter-widgets/jupyterlab-manager@0.38.0
```

### Tests

This runs mypy and tests, and reports coverage.

```bash
pytest --cov --mypy
# open coverage file
open htmlcov/index.html
```

You can also test that the documentation notebooks run correctly, but this
[must be run separately from the code coverage](https://github.com/computationalmodelling/nbval/issues/116):

```bash
pytest docs/*.ipynb --nbval
```

### Docs

```bash
sphinx-autobuild docs docs/_build/html/
```
