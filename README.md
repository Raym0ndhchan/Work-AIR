# Work-AIR ADSB Collector

Manual, config-driven ADSB.lol aircraft collection for fixed windows (default: 5 minutes).

## What this does

- Collects **aircraft-only** data from ADSB.lol.
- Supports filters via config (`all`, `mil`, `pia`, `ladd`, `type`, `squawk`, etc.).
- Runs **only when explicitly requested** (`--run` flag).
- Writes run outputs to timestamped folders.

## Quick start

1. Create your runtime config:

```bash
cp adsb_collect_config.example.json adsb_collect_config.json
```

2. Edit selector mode and collection settings in `adsb_collect_config.json`.

3. Run collection manually:

```bash
python3 collect_adsb.py --config adsb_collect_config.json --run
```

Without `--run`, the script exits without pulling data.

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

## Schema profiles

- `core`: minimal operational fields
- `extended`: core + commonly available extended fields
- `full`: includes advanced ADS-B quality/integrity/intent fields (nullable if source does not expose)

Set under:

```json
"schema": {
  "profile": "extended",
  "include_null_advanced": true
}
```

## Output layout

Each run creates:

- `data/adsb_runs/<run_id>/aircraft_events.ndjson` (all observations)
- `data/adsb_runs/<run_id>/latest_aircraft.ndjson` (latest by ICAO24)
- `data/adsb_runs/<run_id>/run_meta.json` (run summary/errors)
- `data/adsb_runs/<run_id>/raw_snapshots/*.json` (if enabled)

## Notes

- Endpoint paths can evolve; if ADSB.lol changes docs, update `MODE_ENDPOINTS` in `collect_adsb.py`.
- Advanced standard fields are included as nullable columns so you can keep a stable schema even when a feed omits them.
