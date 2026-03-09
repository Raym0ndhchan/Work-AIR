# Work-AIR ADSB Collector

Manual, config-driven ADSB.lol aircraft collection for fixed windows (default: 5 minutes).

## What this does

- Collects **aircraft-only** data from ADSB.lol.
- Supports filters via config (`all`, `mil`, `pia`, `ladd`, `type`, `squawk`, etc.).
- Runs **only when explicitly requested** (`--run` flag).
- Writes run outputs to timestamped folders in both **NDJSON and CSV**.

## Run in GitHub Codespaces (copy/paste)

```bash
# Go to your repo root (works even if path differs)
cd "$(git rev-parse --show-toplevel)"

# Create config
cp adsb_collect_config.example.json adsb_collect_config.json

# Optional: edit settings (mode, duration, poll interval)
nano adsb_collect_config.json

# Run collection (only runs when --run is provided)
python3 collect_adsb.py --config adsb_collect_config.json --run
```

Dry run (no data pull):

```bash
python3 collect_adsb.py --config adsb_collect_config.json
```

## Selector modes

In `selector.mode`:

- `all` (default)
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
2. Try mode `mil` or another specific endpoint.
3. Set `selector.endpoint_override` to an endpoint path known to work from ADSB.lol docs.

## Notes

- Endpoint paths can evolve; update `MODE_ENDPOINTS` in `collect_adsb.py` when ADSB.lol changes docs.
- Advanced standard fields are included as nullable columns so schema stays stable when feed fields are missing.
