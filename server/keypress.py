"""Keyboard simulation for stratagem input via pynput.

NOTE: pynput only works on Windows for injecting keys into games.
      This module is intentionally importable from WSL (for tests) via try/except.
      In WSL, execute_stratagem() will raise RuntimeError if called.
"""

import threading
import time

try:
    from pynput.keyboard import Controller, Key, KeyCode
    _PYNPUT_AVAILABLE = True
except Exception:
    Controller = None  # type: ignore[assignment,misc]
    Key = None         # type: ignore[assignment]
    KeyCode = None     # type: ignore[assignment,misc]
    _PYNPUT_AVAILABLE = False

# Use Virtual Key codes (from_vk) instead of raw characters.
# Raw char strings trigger KEYEVENTF_UNICODE which some games (DirectInput)
# don't see reliably. VK codes send standard WM_KEYDOWN events that games
# always receive — and avoid OS hotkey interception (Ctrl+W, Ctrl+S, etc.).
#
# VK codes: W=0x57  A=0x41  S=0x53  D=0x44
def _build_key_map() -> dict:
    if KeyCode is None:
        return {"up": "w", "down": "s", "left": "a", "right": "d"}
    return {
        "up":    KeyCode.from_vk(0x57),  # W
        "down":  KeyCode.from_vk(0x53),  # S
        "left":  KeyCode.from_vk(0x41),  # A
        "right": KeyCode.from_vk(0x44),  # D
    }

_KEY_MAP = _build_key_map()

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
            key = _KEY_MAP[direction]
            keyboard.press(key)
            keyboard.release(key)
            time.sleep(key_delay)

        keyboard.release(Key.ctrl)

    finally:
        _lock.release()

    return True


def is_available() -> bool:
    """Return True if pynput is available and key simulation can be used."""
    return _PYNPUT_AVAILABLE
