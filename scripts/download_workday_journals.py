#!/usr/bin/env python3
"""Download Workday journal data for month-end reporting."""

from __future__ import annotations

import argparse
import calendar
import csv
import datetime as dt
import json
import os
from pathlib import Path
from typing import Any
from urllib import parse, request


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download journal data from Workday for a target month."
    )
    parser.add_argument(
        "--year",
        type=int,
        help="4-digit year for the reporting period. Defaults to previous month.",
    )
    parser.add_argument(
        "--month",
        type=int,
        choices=range(1, 13),
        help="1-12 month for the reporting period. Defaults to previous month.",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory where files are written (default: output).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="HTTP timeout in seconds.",
    )
    return parser.parse_args()


def resolve_reporting_period(year: int | None, month: int | None) -> tuple[int, int]:
    if (year is None) != (month is None):
        raise ValueError("year and month must both be provided, or both omitted")

    if year is not None and month is not None:
        return year, month

    today = dt.date.today().replace(day=1)
    prior_month_last_day = today - dt.timedelta(days=1)
    return prior_month_last_day.year, prior_month_last_day.month


def month_date_range(year: int, month: int) -> tuple[dt.date, dt.date]:
    last_day = calendar.monthrange(year, month)[1]
    return dt.date(year, month, 1), dt.date(year, month, last_day)


def _get_json(url: str, headers: dict[str, str], timeout: int) -> dict[str, Any]:
    req = request.Request(url, headers=headers, method="GET")
    with request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_journals(
    base_url: str,
    tenant: str,
    token: str,
    from_date: dt.date,
    to_date: dt.date,
    timeout: int,
) -> list[dict[str, Any]]:
    endpoint = f"{base_url.rstrip('/')}/ccx/api/v1/{tenant}/financialAccounting/journalEntries"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    params = {
        "fromAccountingDate": from_date.isoformat(),
        "toAccountingDate": to_date.isoformat(),
        "limit": 100,
    }

    records: list[dict[str, Any]] = []
    next_url: str | None = f"{endpoint}?{parse.urlencode(params)}"

    while next_url:
        payload = _get_json(next_url, headers, timeout)

        entries = payload.get("data", [])
        records.extend(entries)

        next_link = payload.get("next")
        if next_link:
            next_url = next_link
        else:
            next_url = None

    return records


def write_outputs(records: list[dict[str, Any]], output_dir: Path, period: str) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"workday_journals_{period}.json"
    csv_path = output_dir / f"workday_journals_{period}.csv"

    json_path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as fp:
        fieldnames = [
            "id",
            "journalNumber",
            "ledger",
            "accountingDate",
            "company",
            "currency",
            "totalDebit",
            "totalCredit",
            "status",
        ]
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()

        for entry in records:
            writer.writerow(
                {
                    "id": entry.get("id"),
                    "journalNumber": entry.get("journalNumber"),
                    "ledger": entry.get("ledger", {}).get("id"),
                    "accountingDate": entry.get("accountingDate"),
                    "company": entry.get("company", {}).get("id"),
                    "currency": entry.get("currency", {}).get("id"),
                    "totalDebit": entry.get("totalDebitAmount"),
                    "totalCredit": entry.get("totalCreditAmount"),
                    "status": entry.get("status"),
                }
            )

    return json_path, csv_path


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Set it locally or configure it as a GitHub Actions secret."
        )
    return value


def main() -> None:
    args = parse_args()

    base_url = _require_env("WORKDAY_BASE_URL")
    tenant = _require_env("WORKDAY_TENANT")
    token = _require_env("WORKDAY_API_TOKEN")

    year, month = resolve_reporting_period(args.year, args.month)
    start_date, end_date = month_date_range(year, month)
    period = f"{year}-{month:02d}"

    records = fetch_journals(
        base_url=base_url,
        tenant=tenant,
        token=token,
        from_date=start_date,
        to_date=end_date,
        timeout=args.timeout,
    )

    output_dir = Path(args.output_dir)
    json_path, csv_path = write_outputs(records, output_dir, period)

    print(f"Downloaded {len(records)} journal entries for {period}")
    print(f"JSON: {json_path}")
    print(f"CSV: {csv_path}")


if __name__ == "__main__":
    main()
