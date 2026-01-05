"""Minimal Streamlit dashboard for the Pomodoro tracker.

Run with:

    streamlit run my_dashboard.py

This app uses the existing scheduler.build_plan to show the plan and
run a short demo countdown. Use the "Fast demo" option to treat 1 real
second as 1 Pomodoro minute (good for demos).
"""
from __future__ import annotations

import time

import streamlit as st

from pomodorotracker import scheduler


st.set_page_config(page_title="Pomodoro Dashboard", layout="centered")

st.title("Pomodoro Dashboard")

with st.sidebar:
    pomodoros = st.number_input("Pomodoros", min_value=1, value=scheduler.DEFAULTS["pomodoros"])
    focus_minutes = st.number_input("Focus minutes", min_value=1, value=scheduler.DEFAULTS["focus_minutes"])
    short_break_minutes = st.number_input("Short break minutes", min_value=1, value=scheduler.DEFAULTS["short_break_minutes"])
    long_break_minutes = st.number_input("Long break minutes", min_value=1, value=scheduler.DEFAULTS["long_break_minutes"])
    fast = st.checkbox("Fast demo (1s per minute)", value=True)


def format_minutes(seconds: int) -> str:
    return f"{seconds // 60} min"


plan = scheduler.build_plan(
    pomodoros=int(pomodoros),
    focus_minutes=int(focus_minutes),
    short_break_minutes=int(short_break_minutes),
    long_break_minutes=int(long_break_minutes),
)

st.subheader("Planned intervals")
for it in plan:
    st.write(f"- {it.label}: {format_minutes(it.duration_seconds)}")

st.write("---")

start = st.button("Start session")

if start:
    status = st.empty()
    try:
        for interval in plan:
            # When fast is enabled, treat 1 real second as 1 Pomodoro minute
            seconds = interval.duration_seconds if not fast else interval.duration_seconds // 60
            for remaining in range(seconds, -1, -1):
                status.markdown(f"### ▶ {interval.label} — {remaining} second(s) remaining")
                # small sleep to allow UI to update; in fast mode this is a quick demo
                time.sleep(1)
        st.success("Session complete! 🎉")
    except Exception:
        st.error("Session interrupted or failed.")
