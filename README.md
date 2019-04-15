# `metadsl`

[![Documentation Status](https://readthedocs.org/projects/metadsl/badge/?version=latest)](https://metadsl.readthedocs.io/en/latest/?badge=latest)


A framework for creating domain specific language libraries in Python.

The end goal is for libraries like NumPy, Dask, Numba, and AutoGraph to be able to share
optimizations and representations, as much as possible.

The MVP is a lazy version of the NumPy API that can execute normally, but creates
an intermediate form that expresses the operations to perform, before performing them.


## [Roadmap](./ROADMAP.md)

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
