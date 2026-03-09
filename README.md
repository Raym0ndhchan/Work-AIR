# Work-AIR ADSB Collector

Manual, config-driven ADSB.lol aircraft collection for fixed windows (default: 5 minutes).

## What this does

- Collects **aircraft-only** data from ADSB.lol (no airport endpoints are used).
- Supports filters via config (`aircraft_global`, `mil`, `pia`, `ladd`, `type`, `squawk`, etc.).
- Runs **only when explicitly requested** (`--run` flag).
- Writes run outputs to timestamped folders in both **NDJSON and CSV**.

## Run in GitHub Codespaces (copy/paste)

```bash
# Go to your repo root (works even if path differs)
cd "$(git rev-parse --show-toplevel)"

# Create config
cp adsb_collect_config.example.json adsb_collect_config.json

# Run with default config (5 min, global aircraft)
python3 collect_adsb.py --config adsb_collect_config.json --run
```

Dry run (no data pull):

```bash
python3 collect_adsb.py --config adsb_collect_config.json
```

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

You can also set `selector.endpoint_override` to force a direct endpoint path when testing API changes.

## Endpoint fallback behavior

For `aircraft_global`, the collector tries these endpoints in order until one works:

1. `/v2/all`
2. `/v2`

This helps when ADSB.lol changes their primary global path.

## Schema profiles

- `core`: minimal operational fields
- `extended`: core + commonly available extended fields
- `full`: includes advanced ADS-B quality/integrity/intent fields (nullable if source does not expose)

## Output layout

Each run creates:

- `data/adsb_runs/<run_id>/aircraft_events.ndjson` (all observations)
- `data/adsb_runs/<run_id>/latest_aircraft.ndjson` (latest by ICAO24)
- `data/adsb_runs/<run_id>/aircraft_events.csv` (all observations)
- `data/adsb_runs/<run_id>/latest_aircraft.csv` (latest by ICAO24)
- `data/adsb_runs/<run_id>/run_meta.json` (run summary/errors)
- `data/adsb_runs/<run_id>/raw_snapshots/*.json` (if enabled)

## Troubleshooting

If you get `Events: 0` with many errors:

1. Open `run_meta.json` and inspect `errors` for HTTP status/body snippets.
2. Verify your network can reach `https://api.adsb.lol`.
3. Set `selector.endpoint_override` to an endpoint path known to work from ADSB.lol docs.

## Notes

- Endpoint paths can evolve; update `MODE_ENDPOINTS` in `collect_adsb.py` when ADSB.lol changes docs.
- Advanced standard fields are included as nullable columns so schema stays stable when feed fields are missing.
