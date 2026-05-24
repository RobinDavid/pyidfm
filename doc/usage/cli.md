# Command-line interface

The CLI is exposed as `pyidfm` once installed. Every command supports `--json`
to emit machine-readable output, and the top-level `--debug` flag for verbose
logging.

## Top-level commands

| Command                | Description                                            |
| ---------------------- | ------------------------------------------------------ |
| `pyidfm update-data`   | Download/refresh the local static datasets.            |
| `pyidfm search lines`  | List lines, optionally filtered by transport mode.     |
| `pyidfm search stops`  | List stops served by a given line.                     |
| `pyidfm traffic`       | Next schedules at a stop (live).                       |
| `pyidfm line-report`   | Traffic disruption reports for a line (live).          |
| `pyidfm messages`      | Traffic messages for a line or stop (live).            |

## `update-data`

Download/refresh the local IDFM static datasets (lines, stops, relations, …).

```console
$ pyidfm update-data
```

This command must be run at least once before any other command can succeed —
on a fresh install the dataset files do not exist yet.

## `search lines`

List the available lines, optionally filtered by transport mode (`metro`,
`tram`, `rail`, `bus`).

```console
$ pyidfm search lines --mode rail
```

JSON output:

```console
$ pyidfm search lines --mode rail --json
```

## `search stops`

List the stops served by a given `LINE_ID` (use `search lines` to find IDs):

```console
$ pyidfm search stops C01742
```

## `traffic`

Get next schedules for a stop. Requires an API key.

```console
$ pyidfm traffic --stop-id "STIF:StopArea:SP:43135:"
```

Filter by destination, direction, or line:

```console
$ pyidfm traffic --stop-id "STIF:StopArea:SP:43135:" \
                 --line-id "STIF:Line::C01742:" \
                 --destination "Gare de Lyon"
```

## `line-report`

Get traffic disruption reports for a line (LINE_ID). Elevator failures are
excluded by default — pass `--include-elevators` to include them.

```console
$ pyidfm line-report C01742
```

## `messages`

Get traffic messages for a line or stop (mutually exclusive). Optionally
filter by channel (`Information`, `Perturbation`, `Commercial`).

```console
$ pyidfm messages --line-id "STIF:Line::C01742:" --channel Perturbation
```

## Usage from LLM agents

The CLI is the recommended entry point for LLM agents: every command supports
`--json` so output is straightforward to parse, and a typical flow is just
three calls — `search lines` → `search stops` → `traffic`
(or `line-report` / `messages`).

See [`SKILL.md`](https://github.com/RobinDavid/pyidfm/blob/main/SKILL.md) in
the repository for the agent skill packaging used during development.
