"""Simple Streamlit Pomodoro dashboard with light/dark themes.

Features:
- Minimal sidebar for durations and a theme selector (light/dark).
- Large centered timer, progress bar, and Start/Pause/Reset buttons.
- Optional task list.
- Plays uploaded alarm file or a generated beep when an interval completes.
"""
from __future__ import annotations

import io
import math
import struct
import time
import wave
from typing import List, Optional

import streamlit as st

from . import scheduler


def format_minutes(seconds: int) -> str:
    return f"{seconds // 60} min"


def build_custom_plan(pomodoros: int, focus_m: int, short_m: int, long_m: int, long_interval: int, repeat: int) -> List[scheduler.Interval]:
    intervals: List[scheduler.Interval] = []
    for _ in range(repeat):
        for index in range(1, pomodoros + 1):
            intervals.append(scheduler.Interval(kind="focus", label=f"Focus {index}", duration_seconds=focus_m * 60))
            if index % long_interval == 0:
                intervals.append(scheduler.Interval(kind="long_break", label="Long break", duration_seconds=long_m * 60))
            else:
                intervals.append(scheduler.Interval(kind="short_break", label=f"Short break {index}", duration_seconds=short_m * 60))
    return intervals


def generate_beep(duration_s: float = 0.5, freq: float = 880.0, volume: float = 0.5, samplerate: int = 44100) -> bytes:
    """Generate a short WAV beep (mono 16-bit PCM) in memory."""
    n_samples = int(samplerate * duration_s)
    amplitude = int(32767 * volume)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        for i in range(n_samples):
            t = i / samplerate
            sample = int(amplitude * math.sin(2 * math.pi * freq * t))
            wf.writeframes(struct.pack("<h", sample))
    return buf.getvalue()


def main() -> None:
    st.set_page_config(page_title="Pomodoro Dashboard", layout="centered")

    st.title("Pomodoro")

    # Sidebar: minimal settings
    with st.sidebar:
        pomodoros = st.number_input("Pomodoros", min_value=1, value=scheduler.DEFAULTS["pomodoros"])
        focus_minutes = st.number_input("Focus minutes", min_value=1, value=scheduler.DEFAULTS["focus_minutes"])
        short_break_minutes = st.number_input("Short break minutes", min_value=1, value=scheduler.DEFAULTS["short_break_minutes"])
        long_break_minutes = st.number_input("Long break minutes", min_value=1, value=scheduler.DEFAULTS["long_break_minutes"])
        long_break_interval = st.number_input("Long break every N pomodoros", min_value=1, value=4)
        repeat = st.number_input("Repeat cycles", min_value=1, value=1)
        fast = st.checkbox("Fast demo (1s per minute)", value=True)
        st.write("---")
        theme = st.selectbox("Theme", ["light", "dark"], index=0)
        st.write("---")
        alarm_file = st.file_uploader("Alarm sound (optional)")

    plan = build_custom_plan(
        pomodoros=int(pomodoros),
        focus_m=int(focus_minutes),
        short_m=int(short_break_minutes),
        long_m=int(long_break_minutes),
        long_interval=int(long_break_interval),
        repeat=int(repeat),
    )

    # Apply a simple light/dark CSS
    css_light = "body {background:#ffffff; color:#111111} .stText {color:#111}")
    css_dark = "body {background:#0b1220; color:#e6eef6} .stText {color:#e6eef6}"
    if theme == "dark":
        st.markdown(f"<style>{css_dark}</style>", unsafe_allow_html=True)
    else:
        st.markdown(f"<style>{css_light}</style>", unsafe_allow_html=True)

    st.subheader("Planned intervals")
    for it in plan:
        st.write(f"- {it.label}: {format_minutes(it.duration_seconds)}")

    st.write("---")

    # Minimal tasks
    if "tasks" not in st.session_state:
        st.session_state.tasks = []
    with st.expander("Tasks"):
        t = st.text_input("New task")
        if st.button("Add") and t:
            st.session_state.tasks.append({"text": t, "done": False})
        for i, task in enumerate(st.session_state.tasks):
            st.checkbox(task["text"], value=task.get("done", False), key=f"task_{i}")

    # Simple CSS for big timer and buttons
    st.markdown(
        """
        <style>
        .big-timer {font-size:56px; font-weight:700; text-align:center; margin: 12px 0}
        div.stButton > button {height:64px; width:100%; font-size:18px}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Session state
    if "current_index" not in st.session_state:
        st.session_state.current_index = 0
    if "running" not in st.session_state:
        st.session_state.running = False
    if "end_time" not in st.session_state:
        st.session_state.end_time = 0.0
    if "remaining" not in st.session_state:
        st.session_state.remaining = 0

    # Current interval
    curr: Optional[scheduler.Interval]
    if st.session_state.current_index < len(plan):
        curr = plan[st.session_state.current_index]
        total_seconds = curr.duration_seconds if not fast else max(1, curr.duration_seconds // 60)
    else:
        curr = None
        total_seconds = 0

    # Controls
    c1, c2, c3 = st.columns([1, 1, 1])
    if c1.button("Start"):
        if curr is not None:
            if st.session_state.remaining > 0:
                st.session_state.end_time = time.time() + st.session_state.remaining
            else:
                st.session_state.end_time = time.time() + total_seconds
            st.session_state.running = True
    if c2.button("Pause"):
        st.session_state.running = False
        if st.session_state.end_time:
            st.session_state.remaining = max(0, int(st.session_state.end_time - time.time()))
    if c3.button("Reset"):
        st.session_state.running = False
        st.session_state.current_index = 0
        st.session_state.end_time = 0.0
        st.session_state.remaining = 0

    status = st.empty()
    prog = st.progress(0)

    if curr is None:
        status.markdown("<div class='big-timer'>No intervals planned</div>", unsafe_allow_html=True)
    else:
        if st.session_state.running:
            remaining = int(st.session_state.end_time - time.time())
            if remaining <= 0:
                status.markdown(f"<div class='big-timer'>✓ {curr.label} complete</div>", unsafe_allow_html=True)
                try:
                    alarm_bytes = alarm_file.read() if alarm_file is not None else generate_beep()
                    st.audio(alarm_bytes)
                except Exception:
                    pass
                st.session_state.current_index += 1
                st.session_state.running = False
                st.session_state.end_time = 0.0
                st.session_state.remaining = 0
                time.sleep(0.8)
                getattr(st, "experimental_rerun")()
            else:
                mins, secs = divmod(remaining, 60)
                elapsed = (total_seconds - remaining) if total_seconds > 0 else 0
                pct = int(min(100, (elapsed / total_seconds) * 100)) if total_seconds > 0 else 0
                status.markdown(f"<div class='big-timer'>▶ {curr.label}: {mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)
                prog.progress(pct)
                time.sleep(1)
                getattr(st, "experimental_rerun")()
        else:
            mins, secs = divmod(st.session_state.remaining if st.session_state.remaining > 0 else total_seconds, 60)
            status.markdown(f"<div class='big-timer'>▶ {curr.label}: {mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)
            prog.progress(0)


if __name__ == "__main__":
    main()
"""Streamlit dashboard module for the Pomodoro tracker.

This dashboard provides configurable timer controls, task tracking, and a
large start/pause/reset UI. It uses an internal plan builder so you can set
how often long breaks occur.
"""
from __future__ import annotations

import time
from typing import List, Optional

import io
import math
import struct
import wave

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

    # Minimal aesthetic: small CSS for big timer/button only
    st.markdown(
        """
        <style>
        /* Large central timer */
        .big-timer {font-size:56px; font-weight:700; text-align:center; margin: 10px 0}
        /* Big buttons */
        div.stButton > button {height:64px; width:100%; font-size:20px}
        /* Slim sidebar */
        .css-1d391kg {padding: 8px}
        </style>
        """,
        unsafe_allow_html=True,
    )

    def generate_beep(duration_s: float = 0.5, freq: float = 880.0, volume: float = 0.5, samplerate: int = 44100) -> bytes:
        """Generate a short WAV beep (mono 16-bit PCM) in memory."""
        n_samples = int(samplerate * duration_s)
        amplitude = int(32767 * volume)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(samplerate)
            for i in range(n_samples):
                t = i / samplerate
                sample = int(amplitude * math.sin(2 * math.pi * freq * t))
                wf.writeframes(struct.pack("<h", sample))
        return buf.getvalue()

    st.subheader("Planned intervals")
    for it in plan:
        st.write(f"- {it.label}: {format_minutes(it.duration_seconds)}")

    st.write("---")

    # Minimal tasks - small list (optional)
    if "tasks" not in st.session_state:
        st.session_state.tasks = []
    with st.expander("Tasks (optional)"):
        new_task = st.text_input("Add task")
        if st.button("Add") and new_task:
            st.session_state.tasks.append({"text": new_task, "done": False})
        for i, t in enumerate(st.session_state.tasks):
            st.checkbox(t["text"], value=t["done"], key=f"task_{i}")

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

    # Big timer display and controls (centered)
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

    # Controls: large single-row buttons for clarity
    cols = st.columns([1, 1, 1])
    if cols[0].button("Start"):
        if curr is not None:
            if st.session_state.remaining > 0:
                st.session_state.end_time = time.time() + st.session_state.remaining
            else:
                st.session_state.end_time = time.time() + total_seconds
            st.session_state.running = True
    if cols[1].button("Pause"):
        st.session_state.running = False
        if st.session_state.end_time:
            st.session_state.remaining = max(0, int(st.session_state.end_time - time.time()))
    if cols[2].button("Reset"):
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
                # play alarm: uploaded file preferred, otherwise use generated beep
                try:
                    if alarm_file is not None:
                        alarm_bytes = alarm_file.read()
                    else:
                        alarm_bytes = generate_beep(duration_s=0.6, freq=880.0, volume=0.6)
                    st.audio(alarm_bytes)
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
                        # Timer display and progress
                        status = st.empty()
                        prog = st.progress(0)
                        if curr is None:
                            status.markdown("<div class='big-timer'>No intervals planned</div>", unsafe_allow_html=True)
                        else:
                            if st.session_state.running:
                                remaining = int(st.session_state.end_time - time.time())
                                if remaining <= 0:
                                    status.markdown(f"<div class='big-timer'>✓ {curr.label} complete</div>", unsafe_allow_html=True)
                                    # play alarm (uploaded preferred)
                                    try:
                                        alarm_bytes = alarm_file.read() if alarm_file is not None else generate_beep()
                                        st.audio(alarm_bytes)
                                    except Exception:
                                        pass
                                    # move to next
                                    st.session_state.current_index += 1
                                    st.session_state.running = False
                                    st.session_state.end_time = 0.0
                                    st.session_state.remaining = 0
                                    time.sleep(0.8)
                                    getattr(st, "experimental_rerun")()
                                else:
                                    mins, secs = divmod(remaining, 60)
                                    elapsed = (total_seconds - remaining) if total_seconds > 0 else 0
                                    pct = int(min(100, (elapsed / total_seconds) * 100)) if total_seconds > 0 else 0
                                    status.markdown(f"<div class='big-timer'>▶ {curr.label}: {mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)
                                    prog.progress(pct)
                                    time.sleep(1)
                                    getattr(st, "experimental_rerun")()
                            else:
                                mins, secs = divmod(st.session_state.remaining if st.session_state.remaining > 0 else total_seconds, 60)
                                status.markdown(f"<div class='big-timer'>▶ {curr.label}: {mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)
                                prog.progress(0)
