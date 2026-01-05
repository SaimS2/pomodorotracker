"""Pomodoro schedule helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class Interval:
    """Represents one focus or break interval."""

    kind: str
    label: str
    duration_seconds: int


@dataclass
class PomodoroPlan:
    """Holds a full Pomodoro schedule."""

    intervals: List[Interval]

    @property
    def total_seconds(self) -> int:
        return sum(interval.duration_seconds for interval in self.intervals)

    def __iter__(self) -> Iterable[Interval]:
        return iter(self.intervals)


DEFAULTS = {
    "pomodoros": 4,
    "focus_minutes": 25,
    "short_break_minutes": 5,
    "long_break_minutes": 15,
}


def build_plan(
    *,
    pomodoros: int = DEFAULTS["pomodoros"],
    focus_minutes: int = DEFAULTS["focus_minutes"],
    short_break_minutes: int = DEFAULTS["short_break_minutes"],
    long_break_minutes: int = DEFAULTS["long_break_minutes"],
) -> PomodoroPlan:
    """Create a Pomodoro plan with the requested durations.

    Args:
        pomodoros: Number of focus sessions.
        focus_minutes: Length of each focus session.
        short_break_minutes: Length of breaks between focus sessions.
        long_break_minutes: Length of the long break after the last session.
    """
    if pomodoros < 1:
        raise ValueError("pomodoros must be at least 1")
    if min(focus_minutes, short_break_minutes, long_break_minutes) <= 0:
        raise ValueError("all durations must be positive")

    intervals: List[Interval] = []
    for index in range(1, pomodoros + 1):
        intervals.append(
            Interval(
                kind="focus",
                label=f"Focus {index}",
                duration_seconds=focus_minutes * 60,
            )
        )
        if index == pomodoros:
            intervals.append(
                Interval(
                    kind="long_break",
                    label="Long break",
                    duration_seconds=long_break_minutes * 60,
                )
            )
        else:
            intervals.append(
                Interval(
                    kind="short_break",
                    label=f"Short break {index}",
                    duration_seconds=short_break_minutes * 60,
                )
            )

    return PomodoroPlan(intervals)
