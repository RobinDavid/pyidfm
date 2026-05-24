# Installation

`pyidfm` is published on [PyPI](https://pypi.org/project/pyidfm/) and targets
Python 3.9+.

```console
$ pip install pyidfm
```

Or, from a checkout of the repository:

```console
$ pip install .
```

## API key

Live endpoints (next schedules, traffic reports, messages) require a free API
key from the IDFM PRIM platform:
<https://prim.iledefrance-mobilites.fr/>.

Once you have a key, expose it via the `IDFM_API_KEY` environment variable
(every CLI command picks it up automatically) or pass it explicitly with the
`--apikey` option:

```console
$ export IDFM_API_KEY="your-key-here"
```

## Static datasets

Lines and stops are resolved from local snapshots of the IDFM open-data
datasets. They are downloaded on first use, but you can refresh them at any
time:

```console
$ pyidfm update-data
```

:::{admonition} Licensing
:class: tip

The IDFM open-data datasets bundled at runtime are redistributed under the
[ODbL](http://vvlibri.org/fr/licence/odbl-10/legalcode/unofficial); the live
PRIM API is covered by the
[Licence Mobilité](https://cloud.fabmob.io/s/eYWWJBdM3fQiFNm).
:::

## Development setup

For contributing or building the documentation locally:

```console
$ git clone https://github.com/RobinDavid/pyidfm
$ cd pyidfm
$ pip install -e ".[dev]"
$ pip install -r doc/requirements.txt
$ sphinx-build -b html doc doc/_build/html
```

Then open `doc/_build/html/index.html` in a browser.
