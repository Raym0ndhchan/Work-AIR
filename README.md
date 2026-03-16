# Work-AIR ADSB Collector

Manual, config-driven ADSB.lol aircraft collection for fixed windows (default: 5 minutes).

## What this does

- Collects **aircraft-only** data from ADSB.lol (no airport endpoints).
- Default mode is `aircraft_global_grid`, which uses many `/v2/point/...` aircraft queries to approximate global coverage.
- Runs only when explicitly requested (`--run`).
- Writes NDJSON + CSV outputs.

## Run in GitHub Codespaces (copy/paste)

```bash
cd "$(git rev-parse --show-toplevel)"
cp adsb_collect_config.example.json adsb_collect_config.json
python3 collect_adsb.py --config adsb_collect_config.json --run
```

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

- `data/adsb_runs/<run_id>/aircraft_events.ndjson`
- `data/adsb_runs/<run_id>/latest_aircraft.ndjson`
- `data/adsb_runs/<run_id>/aircraft_events.csv`
- `data/adsb_runs/<run_id>/latest_aircraft.csv`
- `data/adsb_runs/<run_id>/run_meta.json`
