"""Lets a console screen redraw itself on an interval while still reacting
instantly if the user wants to stop -- used by the production line view's
real-time mode (see CLAUDE.md: stdlib only, no external UI libraries)."""

import os
import sys
import time


def clear_screen() -> None:
    """Wipes the console so each live-view refresh redraws in place
    instead of scrolling the previous frame up forever."""
    os.system("cls" if os.name == "nt" else "clear")


def wait_for_enter_or_timeout(seconds: float) -> bool:
    """Blocks up to `seconds`. Returns True the moment Enter is pressed
    (caller should stop refreshing), or False once the timeout elapses
    with nothing typed (caller should redraw and wait again)."""
    if os.name == "nt":
        return _wait_windows(seconds)
    return _wait_posix(seconds)


def _wait_windows(seconds: float) -> bool:
    import msvcrt

    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if msvcrt.kbhit():
            while msvcrt.kbhit():
                msvcrt.getch()
            return True
        time.sleep(0.05)
    return False


def _wait_posix(seconds: float) -> bool:
    import select

    ready, _, _ = select.select([sys.stdin], [], [], seconds)
    if ready:
        sys.stdin.readline()
        return True
    return False
