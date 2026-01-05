"""Streamlit dashboard module for the Pomodoro tracker.

This dashboard provides configurable timer controls, task tracking, and a
large start/pause/reset UI. It uses an internal plan builder so you can set
how often long breaks occur.
"""
from __future__ import annotations

import time
from typing import List, Optional

import streamlit as st

from . import scheduler


def format_minutes(seconds: int) -> str:
    return f"{seconds // 60} min"


def build_custom_plan(pomodoros: int, focus_m: int, short_m: int, long_m: int, long_interval: int, repeat: int) -> List[scheduler.Interval]:
    intervals: List[scheduler.Interval] = []
    for r in range(repeat):
        for index in range(1, pomodoros + 1):
            intervals.append(scheduler.Interval(kind="focus", label=f"Focus {index}", duration_seconds=focus_m * 60))
            if index % long_interval == 0:
                intervals.append(scheduler.Interval(kind="long_break", label="Long break", duration_seconds=long_m * 60))
            else:
                intervals.append(scheduler.Interval(kind="short_break", label=f"Short break {index}", duration_seconds=short_m * 60))
    return intervals


def main() -> None:
    st.set_page_config(page_title="Pomodoro Dashboard", layout="centered")

    st.title("Pomodoro Dashboard")

    # Sidebar: settings
    with st.sidebar:
        pomodoros = st.number_input("Pomodoros", min_value=1, value=scheduler.DEFAULTS["pomodoros"])
        focus_minutes = st.number_input("Focus minutes", min_value=1, value=scheduler.DEFAULTS["focus_minutes"])
        short_break_minutes = st.number_input("Short Break minutes", min_value=1, value=scheduler.DEFAULTS["short_break_minutes"])
        long_break_minutes = st.number_input("Long Break minutes", min_value=1, value=scheduler.DEFAULTS["long_break_minutes"])
        long_break_interval = st.number_input("Long Break interval (every N Pomodoros)", min_value=1, value=4)
        auto_start_breaks = st.checkbox("Auto Start Breaks", value=True)
        auto_start_pomodoros = st.checkbox("Auto Start Pomodoros", value=False)
        auto_check_tasks = st.checkbox("Auto Check Tasks", value=True)
        check_to_bottom = st.checkbox("Check to Bottom (move completed tasks)", value=True)
        repeat = st.number_input("Repeat cycles", min_value=1, value=1)
        fast = st.checkbox("Fast demo (1s per minute)", value=True)
        st.write("---")
        st.write("Sound settings")
        alarm_file = st.file_uploader("Alarm sound (wav/mp3)")
        alarm_volume = st.slider("Alarm volume", 0, 100, 50)
        ticking_file = st.file_uploader("Ticking sound (optional)")
        ticking_volume = st.slider("Ticking volume", 0, 100, 50)
        st.write("---")
        theme = st.selectbox("Theme", ["light", "dark", "blue", "green"], index=0)

    plan = build_custom_plan(
        pomodoros=int(pomodoros),
        focus_m=int(focus_minutes),
        short_m=int(short_break_minutes),
        long_m=int(long_break_minutes),
        long_interval=int(long_break_interval),
        repeat=int(repeat),
    )

    st.subheader("Planned intervals")
    for it in plan:
        st.write(f"- {it.label}: {format_minutes(it.duration_seconds)}")

    st.write("---")

    # Tasks area
    if "tasks" not in st.session_state:
        st.session_state.tasks = []

    with st.expander("Tasks"):
        new_task = st.text_input("New task")
        if st.button("Add task") and new_task:
            st.session_state.tasks.append({"text": new_task, "done": False})
        # Render tasks
        for i, t in enumerate(st.session_state.tasks):
            checked = st.checkbox(t["text"], value=t["done"], key=f"task_{i}")
            if checked != t["done"]:
                st.session_state.tasks[i]["done"] = checked

    # Inject CSS to make the main button big
    st.markdown(
        """
        <style>
        div.stButton > button {height:80px;width:100%;font-size:28px}
        .big-timer {font-size:64px;font-weight:700;text-align:center}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Big timer display and controls
    if "current_index" not in st.session_state:
        st.session_state.current_index = 0
    if "running" not in st.session_state:
        st.session_state.running = False
    if "end_time" not in st.session_state:
        st.session_state.end_time = 0.0
    if "remaining" not in st.session_state:
        st.session_state.remaining = 0

    # Display main timer
    curr: Optional[scheduler.Interval]
    if st.session_state.current_index < len(plan):
        curr = plan[st.session_state.current_index]
        total_seconds = curr.duration_seconds if not fast else curr.duration_seconds // 60
    else:
        curr = None
        total_seconds = 0

    # Controls
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("Start/Resume"):
            if curr is not None:
                # resume from remaining if paused
                if st.session_state.remaining > 0:
                    st.session_state.end_time = time.time() + st.session_state.remaining
                else:
                    st.session_state.end_time = time.time() + total_seconds
                st.session_state.running = True
    with col2:
        if st.button("Pause"):
            st.session_state.running = False
            if st.session_state.end_time:
                st.session_state.remaining = max(0, int(st.session_state.end_time - time.time()))
    with col3:
        if st.button("Reset"):
            st.session_state.running = False
            st.session_state.current_index = 0
            st.session_state.end_time = 0.0
            st.session_state.remaining = 0

    status = st.empty()
    if curr is None:
        st.write("No intervals planned.")
    else:
        if st.session_state.running:
            remaining = int(st.session_state.end_time - time.time())
            if remaining <= 0:
                # interval complete
                status.markdown(f"### ✓ {curr.label} complete")
                # play alarm if provided
                try:
                    if alarm_file is not None:
                        alarm_bytes = alarm_file.read()
                        st.audio(alarm_bytes, format=None)
                except Exception:
                    pass
                # Auto check task
                if auto_check_tasks and st.session_state.tasks:
                    for idx, t in enumerate(st.session_state.tasks):
                        if not t["done"]:
                            st.session_state.tasks[idx]["done"] = True
                            if check_to_bottom:
                                st.session_state.tasks.append(st.session_state.tasks.pop(idx))
                            break
                # move to next
                st.session_state.current_index += 1
                st.session_state.running = False
                st.session_state.end_time = 0.0
                st.session_state.remaining = 0
                # auto-start logic
                if st.session_state.current_index < len(plan):
                    next_interval = plan[st.session_state.current_index]
                    if next_interval.kind.startswith("short_break") or next_interval.kind == "long_break":
                        if auto_start_breaks:
                            st.session_state.running = True
                            secs = next_interval.duration_seconds if not fast else next_interval.duration_seconds // 60
                            st.session_state.end_time = time.time() + secs
                    else:
                        if auto_start_pomodoros:
                            st.session_state.running = True
                            secs = next_interval.duration_seconds if not fast else next_interval.duration_seconds // 60
                            st.session_state.end_time = time.time() + secs
                time.sleep(1)
                st.experimental_rerun()
            else:
                mins, secs = divmod(remaining, 60)
                status.markdown(f"<div class='big-timer'>▶ {curr.label}: {mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)
                time.sleep(1)
                st.experimental_rerun()
        else:
            # not running
            if st.session_state.remaining > 0:
                mins, secs = divmod(st.session_state.remaining, 60)
                status.markdown(f"<div class='big-timer'>▶ {curr.label}: {mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)
            else:
                mins, secs = divmod(total_seconds, 60)
                status.markdown(f"<div class='big-timer'>▶ {curr.label}: {mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
