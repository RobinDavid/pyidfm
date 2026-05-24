# pyidfm CLI reference

Exhaustive flag list for every `pyidfm` command. Loaded on demand from `SKILL.md`.

Global:

- `--debug` — verbose logging on stderr. Place **before** the subcommand.
- All output-bearing subcommands accept `--json` for machine-parseable output.

## `pyidfm update-data`

Download / refresh the local static datasets (lines, stops, line→stop relations).

- No flags. No API key required. Safe to call once at session start if static lookups are failing.

## `pyidfm search lines [NAME_FILTER] [--mode MODE] [--json]`

List static lines.

- `NAME_FILTER` — optional positional. Case-insensitive substring match on the line `name`. The `name` is the short label only — `1`, `7B`, `A`, `T3`, `H`, `21` — **not** `Métro 1` / `RER A` / `Tram T3`. Substring means `1` also matches `10`–`14`; combine with `--mode` to disambiguate (e.g. `--mode metro 1` vs. `--mode tram T1`). Omit to list every line.
- `--mode` — one of `metro`, `tram`, `rail`, `bus`. Omit to list every mode.
- `--json` — JSON array of `{mode, name, id}`.

`id` is the form to pass to `search stops` and as `--line-id`/positional arg of `line-report`.

## `pyidfm search stops LINE_ID [NAME_FILTER] [--json]`

List stops of a line.

- `LINE_ID` — positional, e.g. `C01742` or `STIF:Line::C01742:` (both accepted).
- `NAME_FILTER` — optional positional. Case-insensitive substring match on the stop `name` (e.g. `Châtelet`, `République`). Omit to list every stop on the line. Exits non-zero if nothing matches.
- `--json` — JSON array of stop dataclasses. Notable fields: `name`, `city`, `stop_id` (StopPoint:Q), `exchange_area_id` (StopArea:SP), `x`, `y`, `zip_code`.

Use `exchange_area_id` as `--stop-id` for `traffic` unless you need a specific platform.

## `pyidfm traffic --stop-id STOP_ID [options]`

Next departures (live).

- `--stop-id` *(required)* — usually a `STIF:StopArea:SP:…` from `search stops`.
- `--apikey` — falls back to `IDFM_API_KEY` env var.
- `--line-id` — narrow to a single line.
- `--destination` — substring match on destination name.
- `--direction` — substring match on direction name.
- `--json` — JSON array of `TrafficData`.

`TrafficData` JSON fields: `line_id`, `stop_point_name`, `destination_name`, `destination_id`, `direction`, `schedule` (ISO UTC, may be `null`), `at_stop` (bool), `platform`, `status` (enum string), `note`, `call_note`.

`status` values: `onTime`, `missed`, `arrived`, `notExpected`, `delayed`, `early`, `cancelled`, `noReport`, `unknown`.

## `pyidfm line-report LINE_ID [options]`

Traffic disruption reports (live).

- `LINE_ID` — positional.
- `--apikey` — falls back to `IDFM_API_KEY`.
- `--include-elevators` — by default elevator failures are filtered. Pass this for accessibility-related questions.
- `--json` — JSON array of `ReportData`.

`ReportData` JSON fields: `id`, `name`, `message`, `periods` (list of `[begin, end]` ISO datetimes, Europe/Paris), `severity` (int), `effect`, `category`, `cause`, `type`.

## `pyidfm messages [options]`

Traffic messages for a line or stop.

- `--apikey` — falls back to `IDFM_API_KEY`.
- `--line-id` *or* `--stop-id` — **mutually exclusive**, exactly one is required.
- `--channel` — one of `Information`, `Perturbation`, `Commercial`. Omit for all.
- `--json` — JSON array of raw message objects (shape comes straight from the PRIM SIRI feed, not a dataclass).
