"""Wrapper to run the package Streamlit dashboard.

This file keeps the previous command used during testing working:

    streamlit run my_dashboard.py

It delegates to `pomodorotracker.streamlit_app.main`.
"""
from __future__ import annotations

from pomodorotracker.streamlit_app import main


if __name__ == "__main__":
    main()
