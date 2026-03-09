# Work-AIR ADSB Collector

Manual, config-driven ADSB.lol aircraft collection for fixed windows (default: 5 minutes).

## What this does

<<<<<<< codex/plan-data-collection-for-adb-s-ixv1pd
- Collects **aircraft-only** data from ADSB.lol (no airport endpoints).
- Default mode is `aircraft_global_grid`, which uses many `/v2/point/...` aircraft queries to approximate global coverage.
- Runs only when explicitly requested (`--run`).
- Writes NDJSON + CSV outputs.
=======
- Collects **aircraft-only** data from ADSB.lol (no airport endpoints are used).
- Supports filters via config (`aircraft_global`, `mil`, `pia`, `ladd`, `type`, `squawk`, etc.).
- Runs **only when explicitly requested** (`--run` flag).
- Writes run outputs to timestamped folders in both **NDJSON and CSV**.
>>>>>>> main

## Run in GitHub Codespaces (copy/paste)

```bash
cd "$(git rev-parse --show-toplevel)"
cp adsb_collect_config.example.json adsb_collect_config.json
python3 collect_adsb.py --config adsb_collect_config.json --run
```

<<<<<<< codex/plan-data-collection-for-adb-s-ixv1pd
## Why your previous run failed

Your environment discovered v2 endpoints like `/v2/mil`, `/v2/pia`, `/v2/point/...`, but **not** a global `/v2/all` endpoint.
So this collector now defaults to `aircraft_global_grid` (point-based global sampling), which avoids needing `/v2/all`.

## Selector modes

- `aircraft_global_grid` (default, recommended)
- `mil`
- `pia`
- `ladd`
- `squawk`
- `type`
- `registration`
- `icao`
- `callsign`
- `point`

## Optional: custom global grid points

Set `selector.global_points` to custom `[lat, lon]` points if you want denser or regional coverage.

Example:

```json
"selector": {
  "mode": "aircraft_global_grid",
  "global_points": [[40, -75], [52, 13], [35, 139]]
}
```

## Output
=======
## If global endpoint fails (404), auto-diagnose

```bash
python3 collect_adsb.py --config adsb_collect_config.json --list-endpoints
```

Then set one endpoint directly in config:

```json
"selector": {
  "mode": "aircraft_global",
  "endpoint_override": "/v2/mil"
}
```

(Use an endpoint you see from `--list-endpoints`; this is just an example.)

## Selector modes

In `selector.mode`:

- `aircraft_global` (default)
- `mil`
- `pia`
- `ladd`
- `squawk` (requires `selector.value`)
- `type` (requires `selector.value`, e.g. `A320`)
- `registration` (requires `selector.value`)
- `icao` (requires `selector.value`)
- `callsign` (requires `selector.value`)
- `point` (requires `selector.geo.lat`, `selector.geo.lon`, optional `radius_nm`)

## Endpoint fallback behavior

For `aircraft_global`, the collector tries these endpoints in order:

1. `/v2/all`
2. `/v2/`
3. `/v2`
4. `/v2/all/`

## Output layout

Each run creates:
>>>>>>> main

- `data/adsb_runs/<run_id>/aircraft_events.ndjson`
- `data/adsb_runs/<run_id>/latest_aircraft.ndjson`
- `data/adsb_runs/<run_id>/aircraft_events.csv`
- `data/adsb_runs/<run_id>/latest_aircraft.csv`
- `data/adsb_runs/<run_id>/run_meta.json`
<<<<<<< codex/plan-data-collection-for-adb-s-ixv1pd
=======
- `data/adsb_runs/<run_id>/raw_snapshots/*.json` (if enabled)
>>>>>>> main
