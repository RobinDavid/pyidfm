# pyidfm — Île-de-France Mobilités API

AI-ready Python API wrapper for the Île-de-France Mobilités open-data API. It
exposes next-schedule lookups, traffic disruption reports and traffic messages
for the Paris / Île-de-France public transport network (Metro, RER, Transilien,
Tram, Bus).

The package is designed both as a regular Python library and as a CLI that is
easy to drive from an LLM agent.

> Part of this codebase (notably the SIRI / Navitia request plumbing in
> `idfm.py` and the dataclasses in `models.py`) is derived from the
> [`idfm-api`](https://pypi.org/project/idfm-api/) package, with heavy
> modifications focused on reliability and LLM-friendliness rather than raw
> feature completeness.

## Installation

```sh
pip install pyidfm
```

Or, from a checkout of this repository:

```sh
pip install .
```

### API key

Live endpoints (next schedules, traffic reports, messages) require a free
API key from the IDFM PRIM platform:
<https://prim.iledefrance-mobilites.fr/>.

Once you have a key, expose it via the `IDFM_API_KEY` environment variable
(every CLI command picks it up automatically) or pass it explicitly with the
`--apikey` option.

```sh
export IDFM_API_KEY="your-key-here"
```

### Static datasets

Lines and stops are resolved from local snapshots of the IDFM open-data
datasets. They are downloaded on first use, but you can refresh them if required.

```sh
pyidfm update-data
```

## CLI usage

The CLI is exposed as `pyidfm` once installed. Top-level commands:

| Command                  | Description                                            |
| ------------------------ | ------------------------------------------------------ |
| `pyidfm update-data`     | Download/refresh the local static datasets.            |
| `pyidfm search lines`    | List lines, optionally filtered by transport mode.     |
| `pyidfm search stops`    | List stops served by a given line.                     |
| `pyidfm traffic`         | Next schedules at a stop (live).                       |
| `pyidfm line-report`     | Traffic disruption reports for a line (live).          |
| `pyidfm messages`        | Traffic messages for a line or stop (live).            |

All commands accept `--json` to emit machine-readable output, and the top-level
`--debug` flag for verbose logging.

### Examples

Find the ID of the RER D:

```sh
pyidfm search lines --mode rail
```

List the stops on a line:

```sh
pyidfm search stops C01742
```

Get the next departures at a stop:

```sh
pyidfm traffic --stop-id "STIF:StopArea:SP:43135:"
```

Get current disruptions on a line:

```sh
pyidfm line-report C01742
```

## Python usage

```python
from pyidfm.idfm import IDFMApi
from pyidfm.dataset import Dataset


# Live data (PRIM API key required)
api = IDFMApi(apikey="your-key-here")

stops = api.get_stops("C01742")
for s in stops:
    print(s.name, s.stop_id)

departures = api.get_traffic("STIF:StopArea:SP:43135:")
for d in departures:
    print(d.schedule, d.destination_name, d.direction)

reports = api.get_line_reports("C01742")
for r in reports:
    print(r.name, r.severity, r.effect)
```

## Usage through LLMs

The CLI is the recommended entry point for LLM agents. A typical flow is three
calls — `search lines` → `search stops` → `traffic` (or `line-report` /
`messages`).

**Output format guidance:**
- **Standard output** (default) — formatted table; use this when reporting
  information to the user.
- **`--json`** — machine-parseable array; use this when extracting a specific
  value (an ID to pass to the next command, a departure time, a status).

See [`SKILL.md`](skills/idfm-mobilite/SKILL.md) in this repository for the
agent skill packaging used during development.


## License

MIT — see [LICENCE](./LICENCE).

The IDFM open-data datasets bundled at runtime are redistributed under the
[ODbL](http://vvlibri.org/fr/licence/odbl-10/legalcode/unofficial); the live
PRIM API is covered by the [Licence Mobilité](https://cloud.fabmob.io/s/eYWWJBdM3fQiFNm).
