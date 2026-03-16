"""Keyboard simulation for stratagem input via pynput.

NOTE: pynput only works on Windows for injecting keys into games.
      This module is intentionally importable from WSL (for tests) via try/except.
      In WSL, execute_stratagem() will raise RuntimeError if called.
"""

import threading
import time

try:
    from pynput.keyboard import Controller, Key
    _PYNPUT_AVAILABLE = True
except Exception:
    Controller = None  # type: ignore[assignment,misc]
    Key = None         # type: ignore[assignment]
    _PYNPUT_AVAILABLE = False

_KEY_MAP: dict[str, str] = {
    "up": "w",
    "down": "s",
    "left": "a",
    "right": "d",
}

_lock = threading.Lock()


def execute_stratagem(
    keys: list[str],
    key_delay: float = 0.05,
    ctrl_delay: float = 0.03,
) -> bool:
    """Press Ctrl, type directional key sequence, release Ctrl.

    Args:
        keys: List of directional inputs, e.g. ["up", "right", "down"].
        key_delay: Seconds to wait between key presses.
        ctrl_delay: Seconds to wait after pressing Ctrl before typing keys.

    Returns:
        True on success.

    Raises:
        RuntimeError: If pynput is not available (WSL/non-Windows environment).
        ValueError: If keys list is empty or contains invalid directions.
        BlockingIOError: If another stratagem is currently being executed.
    """
    if not _PYNPUT_AVAILABLE:
        raise RuntimeError(
            "pynput is not available. Run the server on Windows to use key simulation."
        )

    if not keys:
        raise ValueError("Key sequence must not be empty")

    invalid = [k for k in keys if k not in _KEY_MAP]
    if invalid:
        raise ValueError(f"Invalid key directions: {invalid}")

    if not _lock.acquire(blocking=False):
        raise BlockingIOError("Another stratagem is currently being executed")

    try:
        keyboard = Controller()

        keyboard.press(Key.ctrl)
        time.sleep(ctrl_delay)

        for direction in keys:
            char = _KEY_MAP[direction]
            keyboard.press(char)
            keyboard.release(char)
            time.sleep(key_delay)

        keyboard.release(Key.ctrl)

    finally:
        _lock.release()

    return True


def is_available() -> bool:
    """Return True if pynput is available and key simulation can be used."""
    return _PYNPUT_AVAILABLE
