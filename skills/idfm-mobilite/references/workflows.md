# Common workflows

Recipes for typical user requests. Each one assumes `IDFM_API_KEY` is exported and `pyidfm` is on `$PATH`. Loaded on demand from `SKILL.md`.

## 1. "When's the next RER D at Montgeron?"

```sh
# 1. Resolve the RER D line ID (rail mode = Transilien & RER)
pyidfm search lines --mode rail --json \
  | jq '.[] | select(.name | test("RER D|D$"; "i"))'
# → id: "STIF:Line::C01728:"

# 2. Find the Montgeron stop
pyidfm search stops C01728 --json \
  | jq '.[] | select(.name | test("Montgeron"; "i"))'
# → exchange_area_id: "STIF:StopArea:SP:47684:"

# 3. Get departures filtered to that line
pyidfm traffic \
  --stop-id "STIF:StopArea:SP:47684:" \
  --line-id "STIF:Line::C01728:" \
  --json
```

Sort the result by `schedule` ascending and report the first few entries, converting `schedule` (UTC) to local Paris time.

## 2. "Is Metro 1 disrupted right now?"

```sh
# Resolve line ID, then ask for reports
pyidfm search lines --mode metro --json | jq '.[] | select(.name == "1")'
# → "STIF:Line::C01371:" (illustrative — confirm from the live output)

pyidfm line-report C01371 --json
```

- Empty array → no disruption.
- Filter on `severity` / `effect` to surface only the relevant ones (`severity` int, lower = less critical; `effect` is human-readable: `SIGNIFICANT_DELAYS`, `NO_SERVICE`, `REDUCED_SERVICE`, …).
- For accessibility questions, repeat with `--include-elevators`.

## 3. "Châtelet — give me the next departures, all lines"

Châtelet exists in several flavours (Metro `Châtelet`, RER `Châtelet–Les Halles`). Ask the user to confirm which station / mode they mean, then:

```sh
# Pick a line you know serves the station (e.g. Metro 1 → C01371)
pyidfm search stops C01371 --json | jq '.[] | select(.name | test("Châtelet"; "i"))'
# Use the returned exchange_area_id with no --line-id to see every line at that stop:
pyidfm traffic --stop-id "STIF:StopArea:SP:…:" --json
```

Group the result client-side by `line_id` and call `pyidfm search lines` once to resolve names if you want to label groups.

## 4. "Any commercial info on Tram T3a?"

```sh
pyidfm search lines --mode tram --json | jq '.[] | select(.name | test("T3a"; "i"))'
pyidfm messages --line-id <LINE_ID> --channel Commercial --json
```

## 5. Fresh environment — first-call bootstrap

If `search lines` or `search stops` returns empty / errors out, the local snapshot may be missing:

```sh
pyidfm update-data
```

Then retry. `update-data` does **not** require an API key.

## 6. Talking to the user about results

- Always echo the resolved IDs back ("RER D = `STIF:Line::C01728:`, Montgeron = `STIF:StopArea:SP:47684:`") so the user can correct you before the live call burns quota.
- Times in `traffic --json` are UTC. Convert to Europe/Paris when reporting.
- A `null` `schedule` is normal for cancelled or status-only entries — don't drop them silently if `status` is `cancelled` or `delayed`.
