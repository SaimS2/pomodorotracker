import pytest

from pomodorotracker import scheduler


def test_build_plan_includes_long_break_after_last_focus():
    plan = scheduler.build_plan(pomodoros=2, focus_minutes=1, short_break_minutes=1, long_break_minutes=2)
    labels = [interval.label for interval in plan]
    assert labels == ["Focus 1", "Short break 1", "Focus 2", "Long break"]
    assert plan.intervals[-1].duration_seconds == 2 * 60


def test_requires_positive_durations():
    with pytest.raises(ValueError):
        scheduler.build_plan(pomodoros=0)
    with pytest.raises(ValueError):
        scheduler.build_plan(focus_minutes=0)


def test_total_seconds_sums_all_intervals():
    plan = scheduler.build_plan(pomodoros=1, focus_minutes=2, short_break_minutes=1, long_break_minutes=3)
    expected = (2 * 60) + (3 * 60)  # one focus and the long break
    assert plan.total_seconds == expected
