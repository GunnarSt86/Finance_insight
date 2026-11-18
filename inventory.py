"""Export complete live table catalogues from Statistics Iceland and SCB.

Usage:
    pip install requests
    python inventory.py --country both

Outputs:
    iceland_tables.csv, sweden_tables.csv

This inventories *tables and their published metadata*, not their statistical values.
Statistics Iceland uses PxWeb API v1; Statistics Sweden uses PxWebApi v2.
"""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ICELAND_BASE = "https://px.hagstofa.is/pxen/api/v1/en/"
SWEDEN_BASE = "https://statistikdatabasen.scb.se/api/v2/tables"
FIELDS = ["country", "subject", "category_path", "table_id", "title",
          "api_url", "first_period", "last_period", "frequency", "updated", "variables"]


def client() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=5, connect=5, read=5, backoff_factor=1.25,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers.update({"User-Agent": "NordicStatisticsCatalogLearningExample/1.0"})
    return s


def get_json(s: requests.Session, url: str, params: dict | None = None):
    response = s.get(url, params=params, timeout=45)
    response.raise_for_status()
    return response.json()


def iceland_catalog(s: requests.Session, pause: float = 0.15):
    """Walk v1 folder tree (type='l'), yielding one row for each table (type='t')."""
    queue = [("", ())]
    seen = set()
    while queue:
        folder, ancestors = queue.pop(0)
        if folder in seen:
            continue
        seen.add(folder)
        url = ICELAND_BASE + quote(folder, safe="/")
        listing = get_json(s, url)
        if not isinstance(listing, list):
            raise ValueError(f"Unexpected Iceland folder response at {url}: {type(listing)}")
        for entry in listing:
            item_id = str(entry.get("id", ""))
            label = entry.get("text") or item_id
            item_type = str(entry.get("type", "")).lower()
            if not item_id:
                continue
            path = f"{folder.rstrip('/')}/{item_id}".lstrip("/")
            if item_type == "l":
                queue.append((path + "/", (*ancestors, label)))
            elif item_type == "t" or item_id.lower().endswith(".px"):
                yield {
                    "country": "Iceland",
                    "subject": ancestors[0] if ancestors else "",
                    "category_path": " / ".join(ancestors),
                    "table_id": item_id,
                    "title": label,
                    "api_url": ICELAND_BASE + quote(path, safe="/"),
                    "first_period": "", "last_period": "", "frequency": "",
                    "updated": entry.get("updated", ""), "variables": "",
                }
        if pause:
            time.sleep(pause)


def sweden_catalog(s: requests.Session, page_size: int = 500, pause: float = 0.35):
    """Follow v2 page metadata until every page has been retrieved."""
    page_number = 1
    while True:
        payload = get_json(s, SWEDEN_BASE, params={
            "lang": "en", "pageNumber": page_number,
            "pageSize": page_size, "includeDiscontinued": "false",
        })
        records = payload.get("tables")
        if not isinstance(records, list):
            raise ValueError(f"Unexpected SCB response page {page_number}: missing tables array")
        for table in records:
            paths = table.get("paths") or []
            # Some tables have several paths; use the first, retaining all IDs in CSV metadata.
            first_path = paths[0] if paths else []
            labels = [p.get("label", "") for p in first_path]
            table_id = str(table.get("id") or "")
            yield {
                "country": "Sweden",
                "subject": labels[0] if labels else table.get("subjectCode", ""),
                "category_path": " / ".join(labels),
                "table_id": table_id,
                "title": table.get("label", ""),
                "api_url": f"{SWEDEN_BASE}/{quote(table_id, safe='')}?lang=en",
                "first_period": table.get("firstPeriod", ""),
                "last_period": table.get("lastPeriod", ""),
                "frequency": table.get("timeUnit", ""),
                "updated": table.get("updated", ""),
                "variables": " | ".join(table.get("variableNames") or []),
            }
        page = payload.get("page") or {}
        total_pages = page.get("totalPages")
        if (total_pages is not None and page_number >= int(total_pages)) or not records:
            break
        if total_pages is None and len(records) < page_size:
            break
        page_number += 1
        if pause:
            time.sleep(pause)


def export(rows, filename: Path) -> int:
    n = 0
    with filename.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
            n += 1
    return n


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country", choices=("iceland", "sweden", "both"), default="both")
    parser.add_argument("--output", default=".", help="Directory for CSV files")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    with client() as s:
        if args.country in ("iceland", "both"):
            n = export(iceland_catalog(s), output / "iceland_tables.csv")
            print(f"Exported {n:,} Iceland tables -> {output / 'iceland_tables.csv'}")
        if args.country in ("sweden", "both"):
            n = export(sweden_catalog(s), output / "sweden_tables.csv")
            print(f"Exported {n:,} Sweden tables -> {output / 'sweden_tables.csv'}")
    print("Compare matched indicators only after checking definitions and units.")


if __name__ == "__main__":
    main()
