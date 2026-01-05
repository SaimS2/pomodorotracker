"""Command line interface for the Pomodoro tracker."""
from __future__ import annotations

import argparse
import sys
import time
from typing import Iterable

from . import scheduler

BANNER = r"""
 ____   ___  __  __  ___   ___   ___   ____   ____   __   ____   ____ 
(  _ \ / __)(  )(  )/ __) / __) / __) (_  _) (_  _) / _\ (  _ \ / ___)
 )   /( (__  )(__)( \__ \( (__ ( (__    )(     )(  /    \ )   / \___ \
(__\_) \___)(______)(___/ \___) \___)  (__)   (__) \_/\_/(__\_) (____/
"""


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a simple Pomodoro timer in your terminal.")
    parser.add_argument("--pomodoros", type=int, default=scheduler.DEFAULTS["pomodoros"], help="number of focus sessions to run")
    parser.add_argument("--focus-minutes", type=int, default=scheduler.DEFAULTS["focus_minutes"], help="minutes per focus session")
    parser.add_argument("--short-break-minutes", type=int, default=scheduler.DEFAULTS["short_break_minutes"], help="minutes per short break")
    parser.add_argument("--long-break-minutes", type=int, default=scheduler.DEFAULTS["long_break_minutes"], help="minutes for the final long break")
    parser.add_argument("--fast", action="store_true", help="treat one real second as one Pomodoro minute (handy for demos)")
    parser.add_argument("--dry-run", action="store_true", help="show the schedule without running timers")
    return parser.parse_args(argv)


def format_time(seconds: int) -> str:
    minutes, remainder = divmod(seconds, 60)
    return f"{minutes:02d}:{remainder:02d}"


def run_interval(interval: scheduler.Interval, *, second_length: int = 60) -> None:
    print(f"\n▶ {interval.label} — {interval.duration_seconds // 60} minute(s)")
    for remaining in range(interval.duration_seconds, -1, -1):
        sys.stdout.write(f"\r{format_time(remaining)} remaining")
        sys.stdout.flush()
        if remaining:
            time.sleep(max(second_length, 1))
    print("\n✓ Done!")


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv or sys.argv[1:])
    plan = scheduler.build_plan(
        pomodoros=args.pomodoros,
        focus_minutes=args.focus_minutes,
        short_break_minutes=args.short_break_minutes,
        long_break_minutes=args.long_break_minutes,
    )

    print(BANNER)
    print("Pomodoros :", args.pomodoros)
    print("Focus     :", args.focus_minutes, "minute(s)")
    print("Short br. :", args.short_break_minutes, "minute(s)")
    print("Long br.  :", args.long_break_minutes, "minute(s)")
    print()

    if args.dry_run:
        print("Planned intervals:")
        for item in plan:
            minutes = item.duration_seconds // 60
            print(f"- {item.label}: {minutes} minute(s)")
        return

    second_length = 1 if args.fast else 60
    print("Press Ctrl+C to exit early. Running timers…")
    try:
        for interval in plan:
            run_interval(interval, second_length=second_length)
    except KeyboardInterrupt:
        print("\nSession interrupted. See you next time!")


if __name__ == "__main__":  # pragma: no cover
    main()
