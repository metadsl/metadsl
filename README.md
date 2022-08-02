# `metadsl`

[![Documentation Status](https://readthedocs.org/projects/metadsl/badge/?version=latest)](https://metadsl.readthedocs.io/en/latest/?badge=latest) [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Quansight-Labs/metadsl/d5565b5?urlpath=lab/tree/Demo.ipynb) [![Test](https://github.com/metadsl/metadsl/actions/workflows/test.yml/badge.svg?branch=master)](https://github.com/metadsl/metadsl/actions/workflows/test.yml)

`metadsl` is an exploration of how we can create deeply embedded domain specific languages in Python, in a way that is type safe (plays nicely with Mypy) and feels ergonomic to Python developers. It is meant to be a building block for other libraries to create their own domain specific languages and compile them to different forms.

## Current Status

It currently is not being actively supported and is in need of a refactor to:

1. Refactor [the type analysis](https://github.com/Quansight-Labs/metadsl/blob/master/metadsl/typing_tools.py) to stop relying on Python's built in type objects and use its own instead.
2. Make "abstractions" (aka functions) a first class citizen, instead of the current approach of embedding them as data.

It also needs a compelling downstream user to help drive further development.

If you are interested in either of these topics, feel free to open an issue or reach out directly.

## Support

The only reason this projects exists was due to the funding and support from Quansight Labs, from 2018 till 2020.

[![Quansight Labs Logo](https://github.com/Quansight-Labs/quansight-labs-site/raw/main/files/images/QuansightLabs_logo_V2.png)](<(https://labs.quansight.org/)>)
