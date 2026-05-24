# PyIDFM

**AI-ready Python API wrapper for the Île-de-France Mobilités open-data API.**

The `pyidfm` module exposes next-schedule lookups, traffic disruption reports and traffic
messages for the Paris / Île-de-France public transport network (Metro, RER,
Transilien, Tram, Bus). It is designed both as a regular Python library and as
a CLI that is easy to drive from an LLM agent.

:::{note}
Part of this codebase (notably the SIRI / Navitia request plumbing in
[`idfm.py`](api/idfm.md) and the dataclasses in [`models.py`](api/models.md))
is derived from the [`idfm-api`](https://pypi.org/project/idfm-api/) package,
with heavy modifications focused on reliability and LLM-friendliness rather
than raw feature completeness.
:::

## Quick start

```console
$ pip install pyidfm
$ export IDFM_API_KEY="your-key-here"
$ pyidfm search lines --mode rail
```

```python
from pyidfm.idfm import IDFMApi

api = IDFMApi(apikey="your-key-here")
for d in api.get_traffic("STIF:StopArea:SP:43135:"):
    print(d.schedule, d.destination_name, d.direction)
```

## Highlights

- {material-regular}`search;1.2em` **Search** lines and stops from a local
  snapshot of the IDFM open-data datasets.
- {material-regular}`schedule;1.2em` **Live schedules** at any stop via the
  SIRI Stop Monitoring endpoint.
- {material-regular}`error;1.2em` **Disruption reports** and traffic messages
  for a line or a stop.
- {material-regular}`smart_toy;1.2em` **LLM-friendly CLI** — every command
  supports `--json`.

## Contents

```{toctree}
:maxdepth: 2
:caption: Usage

usage/installation
usage/cli
usage/python
```

```{toctree}
:maxdepth: 2
:caption: API reference

api/index
```

## Indices

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`
