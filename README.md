# Work-AIR ADSB Collector

Manual, config-driven ADSB.lol aircraft collection for fixed windows (default: 5 minutes).

## What this does

- Collects **aircraft-only** data from ADSB.lol (no airport endpoints are used).
- Supports filters via config (`aircraft_global`, `mil`, `pia`, `ladd`, `type`, `squawk`, etc.).
- Runs **only when explicitly requested** (`--run` flag).
- Writes run outputs to timestamped folders in both **NDJSON and CSV**.

## Run in GitHub Codespaces (copy/paste)

```bash
cd "$(git rev-parse --show-toplevel)"
cp adsb_collect_config.example.json adsb_collect_config.json
python3 collect_adsb.py --config adsb_collect_config.json --run
```

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

- `data/adsb_runs/<run_id>/aircraft_events.ndjson`
- `data/adsb_runs/<run_id>/latest_aircraft.ndjson`
- `data/adsb_runs/<run_id>/aircraft_events.csv`
- `data/adsb_runs/<run_id>/latest_aircraft.csv`
- `data/adsb_runs/<run_id>/run_meta.json`
- `data/adsb_runs/<run_id>/raw_snapshots/*.json` (if enabled)
