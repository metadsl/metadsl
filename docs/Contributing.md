# Contributing

## Development

Either use repo2docker:

```bash
repo2docker -E .
```

Or get started with Conda/flit:

```bash
conda env create -f binder/environment.yml
conda activate metadsl
flit -f typez.pyproject.toml install --symlink
flit install --symlink
flit -f rewrite.pyproject.toml install --symlink
flit -f core.pyproject.toml install --symlink
flit -f visualize.pyproject.toml install --symlink
flit -f llvm.pyproject.toml install --symlink
flit -f numpy.pyproject.toml install --symlink
flit -f python.pyproject.toml install --symlink
flit -f all.pyproject.toml install --symlink

# optional
jupyter labextension install ./typez
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

You can also run tests through ipython, to test if the custom visualizations all work:

```bash
ipython -m pytest
```

If you want to test against all our supported Python versions, we support using
pytest xdist and conda to do that:

```bash
make test
```

Currently this just runs the `metadsl_python` tests.

### Debugging

If you have a notebook that isn't working, one way to debug it is to convert it to a Python
script, and then run that python script with `pudb`.

```bash
jupyter nbconvert --to script Notebook.ipynb
python -m pudb Notebook.py
```

### Docs

```bash
sphinx-autobuild docs docs/_build/html/
```

### Requirements

You can generate a new `environment.yml` from our project dependencies with:

```bash
beni --deps all pyproject.toml *.pyproject.toml > binder/environment.yml
```

### Publishing

First bump all versions in Python and JS packages.

```bash
cd typez
npm publish
cd ..
flit -f typez.pyproject.toml publish
flit -f pyproject.toml publish
flit -f rewrite.pyproject.toml publish
flit -f core.pyproject.toml   publish
flit -f visualize.pyproject.toml   publish
flit -f llvm.pyproject.toml   publish
flit -f python.pyproject.toml   publish
flit -f all.pyproject.toml    publish
```
