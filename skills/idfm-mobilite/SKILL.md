---
name: idfm-mobilite
description: Query live Paris / Île-de-France public transport (Metro, RER, Transilien, Tram, Bus) via the pyidfm CLI — next departures at a stop, traffic disruptions on a line, and traffic messages. Use whenever the user asks about Paris transit, IDFM, Île-de-France Mobilités, the RATP/SNCF/Transilien network, the next train/bus, or any line/stop status in the Île-de-France region.
license: MIT
---

# idfm-mobilite

Drive the `pyidfm` CLI to answer questions about Île-de-France public transport in real time.

## When to use this skill

Trigger on any of:

- "Next train / metro / RER / bus at <stop>"
- "Is the RER A / Metro 1 / Tram T3 disrupted?"
- "Traffic on line X in Paris / Île-de-France"
- Any mention of IDFM, Île-de-France Mobilités, PRIM, Transilien, RATP, SNCF Île-de-France
- Stop or line IDs of the form `STIF:StopArea:SP:…`, `STIF:StopPoint:Q:…`, `STIF:Line::C…`

## Setup (one-time, then cached)

1. **Install** — `pip install pyidfm` (exposes the `pyidfm` CLI).
2. **API key** — live endpoints need a free PRIM key from <https://prim.iledefrance-mobilites.fr/>. Export it:
   ```sh
   export IDFM_API_KEY="your-key-here"
   ```
   Every command picks it up automatically; `--apikey` overrides it.
3. **Static data** — lines and stops are resolved from local snapshots that download on first use. Refresh with `pyidfm update-data` if needed (no API key required).

If `IDFM_API_KEY` is not set when a live command is invoked, ask the user for it before retrying — do not invent one.

## Core flow

Almost every question resolves to this three-step pattern. **Always use the CLI command line**; reach for the Python API only as a last resort when scripting in Python is strictly required (see [Python API — last resort](#python-api--last-resort) at the end of this document).

**Output format:**
- **Standard output** (default, no flag) — formatted Rich table; use this when reporting information to the user.
- **`--json`** — machine-parseable JSON array; use this when you need to extract a specific value (an ID to pass to the next command, a departure time, a status).

```
# Steps 1 & 2: use --json to extract IDs for chaining
1. pyidfm search lines [NAME_FILTER] --mode <metro|rail|tram|bus> --json   → find LINE_ID
2. pyidfm search stops <LINE_ID> [NAME_FILTER] --json                      → find STOP_ID (exchange_area_id)

# Step 3: standard output to report to user; --json to extract a specific field
3. pyidfm traffic --stop-id <STOP_ID> --line-id <LINE_ID>                  → live departures (table)
   pyidfm traffic --stop-id <STOP_ID> --line-id <LINE_ID> --json           → live departures (JSON)
```

Both `search` commands take an optional positional `NAME_FILTER` (case-insensitive substring match on the `name` field). Use it whenever the user already named a line or stop, to keep the JSON small and parseable.

The line `name` is the short label only — `"1"`, `"7B"`, `"A"`, `"T3"`, `"H"`, `"21"` — **not** `"Métro 1"`, `"RER A"`, or `"Tram T3"`. Combine with `--mode` to disambiguate when the label is reused across modes (e.g. metro `1` vs. tram `T1`, or the short bus number `1`). Examples:

- `pyidfm search lines 1 --mode metro --json` → just metro line 1 (substring also matches 10–14, so inspect the JSON or tighten with `--mode`).
- `pyidfm search lines A --mode rail --json` → RER A.
- `pyidfm search lines T3 --mode tram --json` → trams T3a / T3b.

The stop `NAME_FILTER` matches the `name` field exactly as it appears in the dataset (e.g. `Châtelet`, `République`, `Gare de Lyon`).

For disruptions, replace step 3 with `pyidfm line-report <LINE_ID> --json`.

## ID formats — read these carefully

| Field returned by              | Format                          | Use as                                         |
| ------------------------------ | ------------------------------- | ---------------------------------------------- |
| `search lines` → `id`          | `STIF:Line::C01742:`            | `--line-id`, positional arg of `line-report`   |
| `search stops` → `stop_id`     | `STIF:StopPoint:Q:42587:`       | A single platform / quay                       |
| `search stops` → `exchange_area_id` | `STIF:StopArea:SP:43135:`  | **Prefer this** for `--stop-id` on `traffic`   |

`exchange_area_id` (the `StopArea`) groups all platforms of a station and is what you almost always want for `traffic`. A bare `StopPoint:Q:` only returns one direction / track.

## Commands at a glance

| Command                | Purpose                                   | Needs key? |
| ---------------------- | ----------------------------------------- | ---------- |
| `update-data`          | Refresh local line/stop datasets          | no         |
| `search lines`         | List lines (optional `--mode`)            | no         |
| `search stops <LINE>`  | List stops of a line                      | no         |
| `traffic`              | Next departures at a stop (live)          | yes        |
| `line-report <LINE>`   | Traffic disruptions on a line (live)      | yes        |
| `messages`             | Traffic messages for a line or stop       | yes        |

Full flag reference: [references/cli-reference.md](references/cli-reference.md).
Worked-out task recipes: [references/workflows.md](references/workflows.md).

## JSON output samples

### `pyidfm search lines --json`

```json
[
  { "mode": "rail", "name": "D", "id": "STIF:Line::C01728:" },
  { "mode": "rail", "name": "A", "id": "STIF:Line::C01742:" }
]
```

### `pyidfm search stops <LINE_ID> --json`

Use `exchange_area_id` (not `stop_id`) when calling `traffic`.

```json
[
  {
    "name": "Montgeron - Crosne",
    "stop_id": "STIF:StopPoint:Q:471656:",
    "x": 2.4611,
    "y": 48.7053,
    "zip_code": "91230",
    "city": "Montgeron",
    "exchange_area_id": "STIF:StopArea:SP:47684:",
    "exchange_area_name": "Montgeron - Crosne"
  }
]
```

### `pyidfm traffic --json`

Returns an array of departure objects. Key fields:
- `line_id` — `STIF:Line::C…`
- `schedule` — ISO 8601 UTC datetime (may be `null` if unknown); convert to Paris time when relaying to user (the standard table output already does this)
- `status` — `onTime`, `delayed`, `cancelled`, `arrived`, `missed`, `notExpected`, `early`, `noReport`, `unknown`
- `destination_name`, `direction` — strings (direction can fall back to destination)
- `stop_point_name`, `platform`, `at_stop` (bool)
- `note`, `call_note` — free-text annotations (e.g. train code, "Métro à l'approche")

```json
[
  {
    "line_id": "STIF:Line::C01728:",
    "stop_point_name": "Montgeron - Crosne",
    "destination_name": "Goussainville",
    "destination_id": "STIF:StopArea:SP:47921:",
    "direction": "Goussainville",
    "schedule": "2026-05-24T08:28:03+00:00",
    "at_stop": false,
    "platform": "2B",
    "status": "onTime",
    "note": "FACA",
    "call_note": ""
  },
  {
    "line_id": "STIF:Line::C01728:",
    "stop_point_name": "Montgeron - Crosne",
    "destination_name": "Melun",
    "destination_id": "STIF:StopArea:SP:47909:",
    "direction": "Melun",
    "schedule": "2026-05-24T08:33:59+00:00",
    "at_stop": false,
    "platform": "1B",
    "status": "onTime",
    "note": "ZHCO",
    "call_note": ""
  }
]
```

### `pyidfm line-report <LINE_ID> --json`

`periods` is a list of `[start_iso, end_iso]` pairs (Paris timezone).

```json
[
  {
    "id": "NAVITIA:disruption:abc123:",
    "name": "Travaux sur la ligne D",
    "message": "Des travaux sont prévus entre Juvisy et Melun les week-ends de mai.",
    "periods": [
      ["2026-05-17T22:00:00+02:00", "2026-05-18T06:00:00+02:00"]
    ],
    "severity": 2,
    "effect": "REDUCED_SERVICE",
    "category": "Travaux",
    "cause": "travaux",
    "type": "trip"
  }
]
```

## Pitfalls

- **`--line-id` and `--stop-id` are mutually exclusive** on `messages`.
- **Elevator failures** are filtered out by default on `line-report`; pass `--include-elevators` if the user asks about accessibility.
- **Stop disambiguation** — multiple cities have stops named "Châtelet" or "République". When the user names a stop, always show them the candidate `name` + `city` from `search stops --json` and let them confirm before calling `traffic`.
- **Stale data** — if `search stops` returns nothing for a known line, run `pyidfm update-data` and retry.
- **Choose the right output format** — standard output (no flag) renders a Rich table suitable for reporting to the user; use `--json` only when extracting a specific field or chaining commands.

## Python API — last resort

Use the CLI for all queries. Use this API only when you need to integrate `pyidfm` into a Python script and the CLI output cannot be piped easily.

```python
from pyidfm.idfm import IDFMApi

api = IDFMApi(apikey="…")
stops = api.get_stops("C01742")                          # line ID without the STIF:Line:: prefix also works
deps = api.get_traffic("STIF:StopArea:SP:43135:")        # → list[TrafficData]
reports = api.get_line_reports("C01742")                 # → list[ReportData]
```

Dataclasses (`TrafficData`, `ReportData`, `StopData`) are documented in `pyidfm/models.py`.
