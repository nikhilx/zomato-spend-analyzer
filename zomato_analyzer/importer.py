"""Incremental import utilities placed in the core package.

Provides functions to run incremental imports from MBOX into the SQLite DB.
The `tools` wrapper should call `run_cli()` or `incremental_import()`.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Iterable, Optional, Tuple

from zomato_analyzer.config import DATA_DIR, MBOX_PATH
from zomato_analyzer.parsers.mbox_parser import MBoxParser
from zomato_analyzer.parsers.zomato import ZomatoEmailParser
from zomato_analyzer.db.database import OrderDatabase


LAST_SYNC_FILE = DATA_DIR / "last_sync.txt"


def read_last_sync(path: Path) -> Optional[datetime]:
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding='utf-8').strip()
        if not text:
            return None
        dt = datetime.fromisoformat(text)
        # ensure timezone-aware in UTC for safe comparisons
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except Exception:
        return None


def write_last_sync(path: Path, dt: datetime) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # normalize to UTC and write ISO (includes offset)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    path.write_text(dt.isoformat(), encoding='utf-8')


def incremental_import(mbox_path: Optional[str] = None, *, force: bool = False) -> Tuple[int, int, int]:
    """Perform an incremental import and return (inserted, updated, skipped).

    If `force` is True, ignore `last_sync` and reprocess all messages (still idempotent).
    """
    mbox_file = mbox_path or MBOX_PATH
    parser = MBoxParser(mbox_file)
    db = OrderDatabase()

    last_sync = None if force else read_last_sync(LAST_SYNC_FILE)

    orders = []
    skipped = 0
    newest_order_dt: Optional[datetime] = last_sync

    for subject, from_addr, body, email_dt in parser.parse():
        if not MBoxParser.validate_email(subject, from_addr):
            continue

        # Normalize parsed email header datetime: treat naive datetimes as IST
        IST = timezone(timedelta(hours=5, minutes=30))
        if email_dt:
            if email_dt.tzinfo is None:
                email_dt = email_dt.replace(tzinfo=IST)
            else:
                email_dt = email_dt.astimezone(IST)
            # convert to UTC for comparison/storage
            email_dt = email_dt.astimezone(timezone.utc)

        if email_dt and last_sync and email_dt <= last_sync:
            skipped += 1
            continue

        order = ZomatoEmailParser.extract_order(subject, from_addr, body, email_dt)
        if not order:
            continue

        # normalize order.order_date to timezone-aware UTC for comparisons
        od = order.order_date
        if od is None:
            # fallback: if order has no date, use email_dt if available
            if email_dt:
                od = email_dt
            else:
                # leave as-is (shouldn't normally happen)
                od = datetime.now(timezone.utc)

        # treat naive order dates as IST, then convert to UTC
        if od.tzinfo is None:
            od = od.replace(tzinfo=IST)
        else:
            od = od.astimezone(IST)
        od = od.astimezone(timezone.utc)
        order.order_date = od

        orders.append(order)

        if newest_order_dt is None or order.order_date > newest_order_dt:
            newest_order_dt = order.order_date

    if not orders:
        return 0, 0, skipped

    inserted, updated, skipped_updates = db.bulk_upsert_orders(orders, upsert=force)

    if newest_order_dt:
        write_last_sync(LAST_SYNC_FILE, newest_order_dt)

    # Combine skipped counts: emails skipped earlier + rows skipped because unchanged
    return inserted, updated, skipped + skipped_updates


def run_cli(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description='Incremental import of Zomato MBOX (core)')
    parser.add_argument('--mbox', '-m', help='Path to MBOX file', default=None)
    parser.add_argument('--force', '-f', action='store_true', help='Force reprocess all emails')
    args = parser.parse_args(list(argv) if argv else None)

    inserted, updated, skipped = incremental_import(args.mbox, force=args.force)
    print(f"Inserted={inserted} Updated={updated} Skipped={skipped}")
    return 0


if __name__ == '__main__':
    raise SystemExit(run_cli())
