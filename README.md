# pomodorotracker

A simple terminal Pomodoro tracker inspired by [pomofocus.io](https://pomofocus.io/).

## Features
- Command-line timer with configurable focus and break lengths
- "Fast" demo mode where one second equals one Pomodoro minute
- Dry-run option to preview the schedule without waiting

## Getting started
1. Create a virtual environment and install the package in editable mode:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```
2. Run the tracker:
   ```bash
   pomodorotracker --pomodoros 4 --focus-minutes 25 --short-break-minutes 5 --long-break-minutes 15
   ```
3. For a quick demo, speed things up:
   ```bash
   pomodorotracker --pomodoros 2 --focus-minutes 1 --short-break-minutes 1 --long-break-minutes 2 --fast
   ```
4. Preview the schedule without starting timers:
   ```bash
   pomodorotracker --dry-run
   ```

## Development
- Run the tests with `pytest`.
- The timer code lives in `src/pomodorotracker/cli.py`; scheduling helpers are in `src/pomodorotracker/scheduler.py`.
