#!/usr/bin/env python3
"""
GivEnergy Cloud Data Dump Tool

Archives all your data from the GivEnergy Cloud API before it goes offline.
Dumps: account info, inverter settings, historical data points, meter data,
events, communication devices, and site data.

Usage:
    python -m givlocal.cli.cloud_dump --token YOUR_API_TOKEN --output ./cloud-dump

This tool is rate-limit aware (300 req/min) and will back off if throttled.
"""

import argparse
import json
import os
import sys
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package required. Install with: pip install requests")
    sys.exit(1)

BASE_URL = "https://api.givenergy.cloud/v1"
RATE_LIMIT_PAUSE = 2  # seconds between paginated requests


class RateLimiter:
    """Sliding-window limiter with a shared backoff gate.

    At most `max_per_min` acquisitions per 60s. On 429, callers invoke
    `pause(seconds)` to force all threads to sleep past a shared deadline
    and clear the window, preventing thundering-herd retries.
    """

    def __init__(self, max_per_min: int):
        self.max = max_per_min
        self.times: deque = deque()
        self.lock = threading.Lock()
        self.pause_until: float = 0.0

    def acquire(self):
        while True:
            with self.lock:
                now = time.monotonic()
                if now < self.pause_until:
                    wait = self.pause_until - now
                else:
                    while self.times and now - self.times[0] >= 60:
                        self.times.popleft()
                    if len(self.times) < self.max:
                        self.times.append(now)
                        return
                    wait = 60 - (now - self.times[0]) + 0.01
            time.sleep(wait)

    def pause(self, seconds: float):
        """Block all callers for `seconds` and clear the request window."""
        with self.lock:
            self.pause_until = max(self.pause_until, time.monotonic() + seconds)
            self.times.clear()


class CloudDumper:
    def __init__(self, token: str, output_dir: str, workers: int = 1, rate_per_min: int = 250):
        self.token = token
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )
        self.request_count = 0
        self.count_lock = threading.Lock()
        self.inverter_serials: list[str] = []
        self.workers = max(1, workers)
        # Clamp rate to the API's documented hard limit of 300/min.
        self.limiter = RateLimiter(min(max(1, rate_per_min), 300))

    def _get(self, path: str, params: dict = None, _retries: int = 2) -> dict | None:
        url = f"{BASE_URL}{path}"
        self.limiter.acquire()
        with self.count_lock:
            self.request_count += 1
        try:
            resp = self.session.get(url, params=params, timeout=30)
            if resp.status_code == 429 and _retries > 0:
                # Shared pause: all threads honor the backoff, and the
                # rate-limiter window is cleared so we don't stampede
                # the API the moment the sleep ends.
                print("  Rate limited (429). All workers pausing 60s...")
                self.limiter.pause(60)
                return self._get(path, params=params, _retries=_retries - 1)
            if resp.status_code in (200, 201):
                return resp.json()
            else:
                print(f"  WARNING: {path} returned {resp.status_code}: {resp.text[:200]}")
                return None
        except Exception as e:
            print(f"  ERROR: {path} failed: {e}")
            return None

    def _get_all_pages(self, path: str, params: dict = None) -> list:
        """Fetch all pages of a paginated endpoint."""
        all_items = []
        page = 1
        while True:
            p = dict(params or {})
            p["page"] = page
            p["pageSize"] = 50
            data = self._get(path, params=p)
            if not data:
                break
            items = data.get("data", [])
            if not items:
                break
            all_items.extend(items)
            meta = data.get("meta", {})
            last_page = meta.get("last_page", 1)
            print(f"    Page {page}/{last_page} ({len(all_items)} items so far)")
            if page >= last_page:
                break
            page += 1
            time.sleep(RATE_LIMIT_PAUSE)
        return all_items

    def _save(self, filename: str, data):
        path = self.output_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"  Saved: {path} ({os.path.getsize(path)} bytes)")

    def dump_account(self):
        print("\n[1/7] Account info...")
        data = self._get("/account")
        if data:
            self._save("account.json", data)

    def dump_communication_devices(self):
        print("\n[2/7] Communication devices...")
        items = self._get_all_pages("/communication-device")
        self._save("communication_devices.json", items)

        # Extract inverter serials for subsequent dumps
        for device in items:
            inv = device.get("inverter", {})
            serial = inv.get("serial")
            if serial:
                self.inverter_serials.append(serial)
                print(f"    Found inverter: {serial}")

    def dump_settings(self, serial: str):
        print(f"\n  [{serial}] Settings list...")
        data = self._get(f"/inverter/{serial}/settings")
        if data:
            self._save(f"inverters/{serial}/settings.json", data)

            # Also read current value of each setting
            settings = data.get("data", [])
            if settings:
                print(f"    Reading {len(settings)} setting values...")
                values = {}
                for i, setting in enumerate(settings):
                    sid = setting.get("id")
                    resp = self._get(f"/inverter/{serial}/settings/{sid}/read")
                    if resp:
                        values[sid] = {
                            "id": sid,
                            "name": setting.get("name"),
                            "validation": setting.get("validation"),
                            "validation_rules": setting.get("validation_rules"),
                            "value": resp.get("data", {}).get("value"),
                        }
                    if (i + 1) % 10 == 0:
                        print(f"      {i + 1}/{len(settings)} settings read")
                    time.sleep(0.5)  # Be gentle with rate limit
                self._save(f"inverters/{serial}/settings_values.json", values)

    def dump_system_data(self, serial: str):
        print(f"\n  [{serial}] Latest system data...")
        data = self._get(f"/inverter/{serial}/system-data-latest")
        if data:
            self._save(f"inverters/{serial}/system_data_latest.json", data)

    def dump_meter_data(self, serial: str):
        print(f"\n  [{serial}] Latest meter data...")
        data = self._get(f"/inverter/{serial}/meter-data-latest")
        if data:
            self._save(f"inverters/{serial}/meter_data_latest.json", data)

    def dump_events(self, serial: str):
        print(f"\n  [{serial}] Events...")
        data = self._get(f"/inverter/{serial}/events")
        if data:
            self._save(f"inverters/{serial}/events.json", data)

    def dump_presets(self, serial: str):
        print(f"\n  [{serial}] Presets...")
        data = self._get(f"/inverter/{serial}/presets")
        if data:
            self._save(f"inverters/{serial}/presets.json", data)

    def dump_health(self, serial: str):
        print(f"\n  [{serial}] Health checks...")
        data = self._get(f"/inverter/{serial}/health")
        if data:
            self._save(f"inverters/{serial}/health.json", data)

    def _fetch_day(self, serial: str, date_str: str) -> tuple[list, bool]:
        """Fetch all paginated points for a single day.

        Returns (points, ok). `ok` is False if any page fetch failed
        (None response), so the caller can distinguish "empty day" from
        "partial fetch" and surface it as a warning.
        """
        day_points: list = []
        page = 1
        ok = True
        while True:
            data = self._get(
                f"/inverter/{serial}/data-points/{date_str}",
                params={"page": page, "pageSize": 100},
            )
            if data is None:
                ok = False
                break
            points = data.get("data", [])
            if not points:
                break
            day_points.extend(points)
            meta = data.get("meta", {})
            last_page = meta.get("last_page", 1)
            if page >= last_page:
                break
            page += 1
        return day_points, ok

    def dump_data_points(self, serial: str, days: int = 365):
        print(f"\n  [{serial}] Historical data points (last {days} days, {self.workers} workers)...")
        today = datetime.now().date()
        dates = [(today - timedelta(days=i)).isoformat() for i in range(days)]
        results: dict[str, list] = {}
        checkpoint_lock = threading.Lock()

        def checkpoint():
            flat = [p for d in dates for p in results.get(d, [])]
            self._save(f"inverters/{serial}/data_points.json", flat)

        if self.workers == 1:
            for i, date_str in enumerate(dates):
                points, ok = self._fetch_day(serial, date_str)
                results[date_str] = points
                if not ok:
                    print(f"    WARNING: {date_str} fetch incomplete (partial or failed)")
                elif not points:
                    print(f"    NOTE: {date_str} returned 0 points")
                if (i + 1) % 30 == 0 or i == 0:
                    total = sum(len(v) for v in results.values())
                    print(f"    {date_str}: {len(points)} points (total: {total})")
                if (i + 1) % 30 == 0:
                    checkpoint()
        else:
            completed = 0
            with ThreadPoolExecutor(max_workers=self.workers) as pool:
                future_to_date = {pool.submit(self._fetch_day, serial, d): d for d in dates}
                for fut in as_completed(future_to_date):
                    d = future_to_date[fut]
                    try:
                        points, ok = fut.result()
                        results[d] = points
                        if not ok:
                            print(f"    WARNING: {d} fetch incomplete (partial or failed)")
                        elif not points:
                            print(f"    NOTE: {d} returned 0 points")
                    except Exception as e:
                        print(f"    ERROR fetching {d}: {e}")
                        results[d] = []
                    completed += 1
                    if completed % 30 == 0 or completed == 1:
                        total = sum(len(v) for v in results.values())
                        print(f"    {completed}/{days} days done ({d}: {len(results[d])}, total: {total})")
                    if completed % 30 == 0:
                        with checkpoint_lock:
                            checkpoint()

        checkpoint()
        total_points = sum(len(v) for v in results.values())
        print(f"    Total: {total_points} data points")

    def dump_sites(self):
        print("\n[6/7] Sites...")
        items = self._get_all_pages("/site")
        self._save("sites.json", items)

        for site in items:
            site_id = site.get("id")
            if site_id:
                data = self._get(f"/site/{site_id}/data-latest")
                if data:
                    self._save(f"sites/{site_id}/data_latest.json", data)
                energy = self._get(f"/site/{site_id}/energy-data-latest")
                if energy:
                    self._save(f"sites/{site_id}/energy_data_latest.json", energy)

    def dump_all(self, days: int = 365):
        print("=" * 60)
        print("GivEnergy Cloud Data Dump")
        print(f"Output: {self.output_dir}")
        print(f"Historical days: {days}")
        print("=" * 60)

        start = time.time()

        # 1. Account
        self.dump_account()

        # 2. Communication devices (also discovers inverter serials)
        self.dump_communication_devices()

        if not self.inverter_serials:
            print("\nWARNING: No inverters found on your account!")
            print("Check your API token has the correct scopes.")
            return

        # 3-5. Per-inverter data
        print(f"\n[3/7] Inverter data ({len(self.inverter_serials)} inverters)...")
        for serial in self.inverter_serials:
            print(f"\n{'=' * 40}")
            print(f"Inverter: {serial}")
            print(f"{'=' * 40}")
            self.dump_settings(serial)
            self.dump_system_data(serial)
            self.dump_meter_data(serial)
            self.dump_events(serial)
            self.dump_presets(serial)
            self.dump_health(serial)

        # Historical data (slowest part)
        print("\n[4/7] Historical data points...")
        for serial in self.inverter_serials:
            self.dump_data_points(serial, days=days)

        print("\n[5/7] Historical meter data...")
        for serial in self.inverter_serials:
            print(f"\n  [{serial}] Meter data history...")
            data = self._get(f"/inverter/{serial}/meter-data")
            if data:
                self._save(f"inverters/{serial}/meter_data_history.json", data)

        # 6. Sites
        self.dump_sites()

        # 7. Summary
        elapsed = time.time() - start
        print(f"\n{'=' * 60}")
        print(f"DONE! {self.request_count} API requests in {elapsed:.0f}s")
        print(f"Data saved to: {self.output_dir}")
        print(f"{'=' * 60}")

        # Save metadata
        self._save(
            "_dump_metadata.json",
            {
                "timestamp": datetime.now().isoformat(),
                "api_requests": self.request_count,
                "elapsed_seconds": round(elapsed),
                "inverter_serials": self.inverter_serials,
                "historical_days": days,
            },
        )


def main():
    parser = argparse.ArgumentParser(
        description="Archive your GivEnergy Cloud data before it goes offline.",
        epilog="Example: python -m givlocal.cli.cloud_dump --token eyJ... --output ./cloud-dump",
    )
    parser.add_argument("--token", required=True, help="GivEnergy Cloud API token (Bearer token)")
    parser.add_argument("--output", default="./cloud-dump", help="Output directory (default: ./cloud-dump)")
    parser.add_argument("--days", type=int, default=365, help="Days of historical data to pull (default: 365)")
    parser.add_argument("--workers", type=int, default=1, help="Parallel workers for data-point fetch (default: 1)")
    parser.add_argument(
        "--rate",
        type=int,
        default=250,
        help="Max API req/min (default: 250, clamped to API limit of 300)",
    )
    parser.add_argument(
        "--settings-only",
        action="store_true",
        help="Only dump settings (fastest, most critical for the local API)",
    )
    args = parser.parse_args()

    dumper = CloudDumper(
        token=args.token,
        output_dir=args.output,
        workers=args.workers,
        rate_per_min=args.rate,
    )

    if args.settings_only:
        print("Settings-only mode: dumping device list and settings")
        dumper.dump_communication_devices()
        for serial in dumper.inverter_serials:
            dumper.dump_settings(serial)
    else:
        dumper.dump_all(days=args.days)


if __name__ == "__main__":
    main()
