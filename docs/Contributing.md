# Contributing

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
