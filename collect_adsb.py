#!/usr/bin/env python3
"""Manual ADSB.lol collection runner.

Runs only when explicitly invoked by the user.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import pathlib
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Iterable, List, Optional, Tuple


MODE_ENDPOINTS = {
    # New default: emulate global by polling multiple point queries.
    "aircraft_global_grid": [],
    "mil": ["/v2/mil", "/v2/mil/"],
    "pia": ["/v2/pia", "/v2/pia/"],
    "ladd": ["/v2/ladd", "/v2/ladd/"],
    "squawk": ["/v2/squawk/{value}", "/v2/sqk/{value}"],
    "type": ["/v2/type/{value}"],
    "registration": ["/v2/registration/{value}", "/v2/reg/{value}"],
    "icao": ["/v2/icao/{value}", "/v2/hex/{value}"],
    "callsign": ["/v2/callsign/{value}"],
    "point": ["/v2/point/{lat}/{lon}/{radius}", "/v2/lat/{lat}/lon/{lon}/dist/{radius}"],
    # Backward compatibility with earlier config versions
    "aircraft_global": [],
    "all": [],
}

OPENAPI_CANDIDATES = ["/openapi.json", "/docs/openapi.json", "/api/openapi.json"]

DEFAULT_GLOBAL_GRID = [
    (-60.0, -150.0),
    (-60.0, -90.0),
    (-60.0, -30.0),
    (-60.0, 30.0),
    (-60.0, 90.0),
    (-60.0, 150.0),
    (-20.0, -150.0),
    (-20.0, -90.0),
    (-20.0, -30.0),
    (-20.0, 30.0),
    (-20.0, 90.0),
    (-20.0, 150.0),
    (20.0, -150.0),
    (20.0, -90.0),
    (20.0, -30.0),
    (20.0, 30.0),
    (20.0, 90.0),
    (20.0, 150.0),
    (60.0, -150.0),
    (60.0, -90.0),
    (60.0, -30.0),
    (60.0, 30.0),
    (60.0, 90.0),
    (60.0, 150.0),
]

CORE_FIELDS = [
    "observed_at",
    "source",
    "selector_mode",
    "icao24",
    "callsign",
    "lat",
    "lon",
    "baro_altitude_ft",
    "ground_speed_kt",
    "track_deg",
    "vertical_rate_fpm",
    "on_ground",
]

EXTENDED_FIELDS = [
    "aircraft_category_code",
    "aircraft_category_text",
    "airspeed_kt",
    "airspeed_type",
    "surveillance_status",
    "emergency_state",
    "gnss_baro_alt_diff_ft",
    "velocity_subtype",
    "heading_deg",
    "squawk",
    "registration",
    "aircraft_type",
]

ADVANCED_FIELDS = [
    "adsb_version",
    "nac_p",
    "nac_v",
    "nic",
    "nic_supplement",
    "sil",
    "sil_supplement",
    "sda",
    "operational_modes",
    "capability_classes",
    "target_altitude_ft",
    "target_heading_or_track_deg",
    "target_is_track",
    "vertical_mode",
    "horizontal_mode",
    "status_subtype",
    "acas_ra",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect aircraft data from ADSB.lol when manually triggered.")
    parser.add_argument("--config", default="adsb_collect_config.json", help="Path to JSON config file")
    parser.add_argument("--run", action="store_true", help="Required safety switch. Collection only starts when this flag is present.")
    parser.add_argument("--list-endpoints", action="store_true", help="Probe OpenAPI endpoint list and exit.")
    return parser.parse_args()


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def load_config(path: pathlib.Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def fetch_json(url: str, timeout_sec: int) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "Work-AIR-collector/1.0"})
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        payload = resp.read().decode("utf-8")
    return json.loads(payload)


def discover_openapi_paths(base_url: str, timeout_sec: int) -> List[str]:
    for suffix in OPENAPI_CANDIDATES:
        url = f"{base_url}{suffix}"
        try:
            spec = fetch_json(url, timeout_sec)
            paths = spec.get("paths")
            if isinstance(paths, dict):
                return sorted(paths.keys())
        except Exception:
            continue
    return []


def build_endpoint_candidates(selector: Dict[str, Any]) -> List[str]:
    endpoint_override = selector.get("endpoint_override")
    if endpoint_override:
        return [str(endpoint_override)]

    mode = selector.get("mode", "aircraft_global_grid")
    if mode not in MODE_ENDPOINTS:
        raise ValueError(f"Unsupported selector.mode '{mode}'. Supported: {', '.join(sorted(MODE_ENDPOINTS))}")

    templates = MODE_ENDPOINTS[mode]
    if mode in {"squawk", "type", "registration", "icao", "callsign"}:
        value = selector.get("value")
        if not value:
            raise ValueError(f"selector.value is required when mode='{mode}'")
        return [template.format(value=value) for template in templates]

    if mode == "point":
        geo = selector.get("geo", {})
        lat = geo.get("lat")
        lon = geo.get("lon")
        radius = geo.get("radius_nm", 250)
        if lat is None or lon is None:
            raise ValueError("selector.geo.lat and selector.geo.lon are required when mode='point'")
        return [template.format(lat=lat, lon=lon, radius=radius) for template in templates]

    return templates


def build_grid_urls(base_url: str, selector: Dict[str, Any]) -> List[str]:
    geo = selector.get("geo", {})
    radius = geo.get("radius_nm", 250)

    points = selector.get("global_points")
    if not isinstance(points, list) or len(points) == 0:
        points = [[lat, lon] for lat, lon in DEFAULT_GLOBAL_GRID]

    urls: List[str] = []
    for point in points:
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            continue
        lat, lon = point
        urls.append(f"{base_url}/v2/point/{lat}/{lon}/{radius}")
    return urls


def pick(obj: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in obj and obj[key] is not None:
            return obj[key]
    return None


def category_text(tc: Optional[int], ca: Optional[int]) -> Optional[str]:
    if tc is None or ca is None:
        return None
    mapping = {(4, 1): "Light", (4, 5): "Heavy", (3, 6): "UAV", (2, 1): "Surface emergency vehicle"}
    return mapping.get((tc, ca))


def extract_aircraft(payload: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    if isinstance(payload.get("aircraft"), list):
        return payload["aircraft"]
    if isinstance(payload.get("ac"), list):
        return payload["ac"]
    if isinstance(payload.get("result"), dict) and isinstance(payload["result"].get("aircraft"), list):
        return payload["result"]["aircraft"]
    return []


def normalize(record: Dict[str, Any], observed_at: str, selector_mode: str, include_advanced: bool) -> Dict[str, Any]:
    tc = pick(record, "type_code", "tc")
    ca = pick(record, "category", "ca")

    row = {
        "observed_at": observed_at,
        "source": "adsb.lol",
        "selector_mode": selector_mode,
        "icao24": pick(record, "hex", "icao24", "icao"),
        "callsign": (pick(record, "flight", "callsign") or "").strip() or None,
        "lat": pick(record, "lat"),
        "lon": pick(record, "lon"),
        "baro_altitude_ft": pick(record, "alt_baro", "baro_altitude", "altitude"),
        "ground_speed_kt": pick(record, "gs", "ground_speed", "speed"),
        "track_deg": pick(record, "track", "trk"),
        "vertical_rate_fpm": pick(record, "baro_rate", "vert_rate", "vertical_rate"),
        "on_ground": pick(record, "ground", "on_ground"),
        "aircraft_category_code": ca,
        "aircraft_category_text": category_text(tc, ca),
        "airspeed_kt": pick(record, "ias", "tas", "airspeed"),
        "airspeed_type": "IAS" if pick(record, "ias") is not None else ("TAS" if pick(record, "tas") is not None else None),
        "surveillance_status": pick(record, "surveillance_status", "ss"),
        "emergency_state": pick(record, "emergency", "emergency_state"),
        "gnss_baro_alt_diff_ft": pick(record, "geom_minus_baro", "gnss_baro_alt_diff_ft"),
        "velocity_subtype": pick(record, "velocity_subtype"),
        "heading_deg": pick(record, "heading", "hdg"),
        "squawk": pick(record, "squawk"),
        "registration": pick(record, "r", "reg", "registration"),
        "aircraft_type": pick(record, "t", "type", "aircraft_type"),
    }

    if include_advanced:
        row.update({
            "adsb_version": pick(record, "version", "adsb_version"),
            "nac_p": pick(record, "nac_p"),
            "nac_v": pick(record, "nac_v"),
            "nic": pick(record, "nic"),
            "nic_supplement": pick(record, "nic_supplement", "nic_s"),
            "sil": pick(record, "sil"),
            "sil_supplement": pick(record, "sil_supplement"),
            "sda": pick(record, "sda"),
            "operational_modes": pick(record, "operational_modes", "op_modes"),
            "capability_classes": pick(record, "capability_classes"),
            "target_altitude_ft": pick(record, "selected_altitude", "target_altitude_ft"),
            "target_heading_or_track_deg": pick(record, "target_heading", "target_track", "target_heading_or_track_deg"),
            "target_is_track": pick(record, "target_is_track"),
            "vertical_mode": pick(record, "vertical_mode"),
            "horizontal_mode": pick(record, "horizontal_mode"),
            "status_subtype": pick(record, "status_subtype"),
            "acas_ra": pick(record, "acas_ra", "ra_active"),
        })

    return row


def ndjson_write(path: pathlib.Path, rows: Iterable[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def csv_write(path: pathlib.Path, rows: List[Dict[str, Any]], columns: List[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col) for col in columns})


def schema_columns(profile: str, include_advanced: bool) -> List[str]:
    columns = CORE_FIELDS.copy()
    if profile in {"extended", "full"}:
        columns.extend(EXTENDED_FIELDS)
    if include_advanced or profile == "full":
        columns.extend(ADVANCED_FIELDS)
    return columns


def ensure_columns(row: Dict[str, Any], profile: str, include_advanced: bool) -> Dict[str, Any]:
    for col in schema_columns(profile, include_advanced):
        row.setdefault(col, None)
    return row


def format_error(exc: Exception) -> Dict[str, Any]:
    if isinstance(exc, urllib.error.HTTPError):
        body_snippet = ""
        try:
            body_snippet = exc.read().decode("utf-8", errors="replace")[:240]
        except Exception:
            body_snippet = ""
        return {"type": "HTTPError", "status": exc.code, "reason": str(exc.reason), "body_snippet": body_snippet}
    return {"type": exc.__class__.__name__, "message": str(exc)}


def choose_working_url(base_url: str, endpoint_candidates: List[str], timeout_sec: int) -> str:
    last_error: Optional[Exception] = None
    for endpoint in endpoint_candidates:
        url = f"{base_url}{endpoint}"
        try:
            fetch_json(url, timeout_sec)
            return url
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code == 404:
                continue
            raise
        except Exception as exc:
            last_error = exc
            raise

    if last_error:
        raise last_error
    raise RuntimeError("No endpoint candidates were provided")


def main() -> int:
    args = parse_args()

    config_path = pathlib.Path(args.config)
    if not config_path.exists():
        print(f"Config not found: {config_path}")
        print("Copy adsb_collect_config.example.json to adsb_collect_config.json and edit values.")
        return 2

    cfg = load_config(config_path)
    source = cfg.get("source", {})
    collect = cfg.get("collect", {})
    selector = cfg.get("selector", {})
    schema = cfg.get("schema", {})

    base_url = str(source.get("base_url", "https://api.adsb.lol")).rstrip("/")
    timeout_sec = int(collect.get("request_timeout_sec", 20))

    if args.list_endpoints:
        paths = discover_openapi_paths(base_url, timeout_sec)
        if not paths:
            print("Could not discover endpoints from OpenAPI.")
            return 4
        print("Discovered API paths:")
        for path in paths:
            print(path)
        return 0

    if not args.run:
        print("No collection performed. Re-run with --run to start pulling data.")
        return 0

    mode = selector.get("mode", "aircraft_global_grid")

    duration_sec = int(collect.get("duration_sec", 300))
    poll_interval_sec = max(1, int(collect.get("poll_interval_sec", 5)))
    out_root = pathlib.Path(str(collect.get("output_dir", "data/adsb_runs")))
    save_raw = bool(collect.get("save_raw_snapshots", True))

    profile = str(schema.get("profile", "extended")).lower()
    include_advanced = bool(schema.get("include_null_advanced", True))
    columns = schema_columns(profile, include_advanced)

    grid_urls: List[str] = []
    single_url: Optional[str] = None

    if mode in {"aircraft_global_grid", "aircraft_global", "all"} and not selector.get("endpoint_override"):
        grid_urls = build_grid_urls(base_url, selector)
        if not grid_urls:
            print("No grid URLs were generated for global mode. Check selector.global_points.")
            return 3
        print(f"Using aircraft global grid mode with {len(grid_urls)} point queries per poll.")
    else:
        endpoint_candidates = build_endpoint_candidates(selector)
        try:
            single_url = choose_working_url(base_url, endpoint_candidates, timeout_sec)
        except Exception as exc:
            print("Unable to resolve a working ADSB endpoint from candidates:")
            for candidate in endpoint_candidates:
                print(f"- {base_url}{candidate}")
            print(f"Failure: {format_error(exc)}")
            discovered = discover_openapi_paths(base_url, timeout_sec)
            if discovered:
                print("\nDiscovered paths (from OpenAPI) you can use with selector.endpoint_override:")
                for path in discovered:
                    if path.startswith("/v2"):
                        print(f"- {path}")
            else:
                print("\nTip: run with --list-endpoints to inspect available paths from your environment.")
            return 3

    run_id = utc_now().strftime("%Y%m%dT%H%M%SZ")
    out_dir = out_root / run_id
    raw_dir = out_dir / "raw_snapshots"
    out_dir.mkdir(parents=True, exist_ok=True)
    if save_raw:
        raw_dir.mkdir(parents=True, exist_ok=True)

    end_time = time.time() + duration_sec
    poll_index = 0
    errors: List[Dict[str, Any]] = []
    events: List[Dict[str, Any]] = []
    latest_by_hex: Dict[str, Dict[str, Any]] = {}

    start_msg = single_url if single_url else f"grid:{len(grid_urls)} endpoints"
    print(f"Starting collection for {duration_sec}s from {start_msg}")

    while time.time() < end_time:
        observed_at = utc_now().isoformat()
        urls_to_poll = [single_url] if single_url else grid_urls

        for url in urls_to_poll:
            if url is None:
                continue
            try:
                payload = fetch_json(url, timeout_sec)
                if save_raw:
                    safe_name = url.replace("https://", "").replace("/", "_").replace("{", "").replace("}", "")
                    snapshot_path = raw_dir / f"snapshot_{poll_index:04d}_{safe_name}.json"
                    snapshot_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

                for ac in extract_aircraft(payload):
                    row = normalize(ac, observed_at, mode, include_advanced)
                    row = ensure_columns(row, profile, include_advanced)
                    icao24 = row.get("icao24")
                    if not icao24:
                        continue
                    events.append(row)
                    latest_by_hex[str(icao24)] = row
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
                errors.append({"observed_at": observed_at, "url": url, **format_error(exc)})

        poll_index += 1
        time.sleep(poll_interval_sec)

    latest_rows = list(latest_by_hex.values())
    ndjson_write(out_dir / "aircraft_events.ndjson", events)
    ndjson_write(out_dir / "latest_aircraft.ndjson", latest_rows)
    csv_write(out_dir / "aircraft_events.csv", events, columns)
    csv_write(out_dir / "latest_aircraft.csv", latest_rows, columns)

    meta = {
        "run_id": run_id,
        "source": "adsb.lol",
        "url": single_url,
        "grid_urls_count": len(grid_urls),
        "duration_sec": duration_sec,
        "poll_interval_sec": poll_interval_sec,
        "polls_completed": poll_index,
        "events_count": len(events),
        "unique_aircraft": len(latest_by_hex),
        "selector": selector,
        "schema": schema,
        "errors": errors,
    }
    (out_dir / "run_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"Done. Output: {out_dir}")
    print(f"Events: {len(events)} | Unique aircraft: {len(latest_by_hex)} | Errors: {len(errors)}")
    if errors:
        print("Sample errors:")
        for err in errors[:3]:
            print(f"- {err}")
    if len(events) == 0:
        print("No aircraft records collected. Check API availability or set selector.endpoint_override.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
