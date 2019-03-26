# `metadsl`

A framework for creating domain specific language libraries in Python.

The end goal is for libraries like NumPy, Dask, Numba, and AutoGraph to be able to share
optimizations and representations, as much as possible.

The MVP is a lazy version of the NumPy API that can execute normally, but creates
an intermediate form that expresses the operations to perform, before performing them.

## Development

```bash
conda create -n metadsl python
conda activate metadsl
pip install flit
flit install --symlink
```


### Docs

```bash
cd docs/
# build
make html
# serve
python -m http.server -d _build/html/
```