"""Keyboard simulation for stratagem input via pynput.

NOTE: pynput only works on Windows for injecting keys into games.
      This module is intentionally importable from WSL (for tests) via try/except.
      In WSL, execute_stratagem() will raise RuntimeError if called.
"""

import logging
import random as _random
import threading
import time

log = logging.getLogger(__name__)

try:
    from pynput.keyboard import Controller, Key, KeyCode
    from pynput.mouse import Button as MouseButton, Controller as MouseController
    _PYNPUT_AVAILABLE = True
except Exception:
    Controller = None      # type: ignore[assignment,misc]
    Key = None             # type: ignore[assignment]
    KeyCode = None         # type: ignore[assignment,misc]
    MouseButton = None     # type: ignore[assignment]
    MouseController = None # type: ignore[assignment,misc]
    _PYNPUT_AVAILABLE = False

# Use Virtual Key codes (from_vk) instead of raw characters.
# Raw char strings trigger KEYEVENTF_UNICODE which some games (DirectInput)
# don't see reliably. VK codes send standard WM_KEYDOWN events that games
# always receive — and avoid OS hotkey interception (Ctrl+W, Ctrl+S, etc.).
#
# VK codes: W=0x57  A=0x41  S=0x53  D=0x44
_VK_CODES: dict[str, int] = {
    "up":    0x57,  # W
    "down":  0x53,  # S
    "left":  0x41,  # A
    "right": 0x44,  # D
}


def _build_key_map() -> dict:
    if KeyCode is None:
        return {"up": "w", "down": "s", "left": "a", "right": "d"}
    return {direction: KeyCode.from_vk(vk) for direction, vk in _VK_CODES.items()}


_KEY_MAP = _build_key_map()

_lock = threading.Lock()


def _random_delay(min_ms: float, max_ms: float) -> float:
    """Sleep for a random duration in [min_ms, max_ms] ms. Returns actual delay in ms."""
    rng = _random.Random(time.time_ns())
    delay = min_ms if max_ms <= min_ms else rng.uniform(min_ms, max_ms)
    time.sleep(delay / 1000.0)
    return delay

# ---------------------------------------------------------------- manual mode

_manual_active = False
_manual_keyboard: object = None   # Controller instance while active
_manual_timer: threading.Timer | None = None
_MANUAL_TIMEOUT_DEFAULT = 3.0     # seconds of inactivity before auto-stop


def _manual_auto_stop() -> None:
    """Called by the inactivity timer — releases Ctrl and resets state."""
    global _manual_active, _manual_keyboard, _manual_timer
    if _manual_keyboard is not None:
        try:
            _manual_keyboard.release(Key.ctrl)
        except Exception:
            pass
    _manual_active = False
    _manual_keyboard = None
    _manual_timer = None
    _lock.release()


def _reset_manual_timer(timeout: float) -> None:
    global _manual_timer
    if _manual_timer is not None:
        _manual_timer.cancel()
    _manual_timer = threading.Timer(timeout, _manual_auto_stop)
    _manual_timer.daemon = True
    _manual_timer.start()


def manual_start(ctrl_delay: float = 0.03, timeout: float = _MANUAL_TIMEOUT_DEFAULT) -> bool:
    """Press and hold Ctrl. Returns False if already active or execute is running.

    Args:
        ctrl_delay: Seconds to wait after pressing Ctrl.
        timeout: Inactivity seconds before Ctrl is auto-released.
    """
    global _manual_active, _manual_keyboard

    if not _PYNPUT_AVAILABLE:
        raise RuntimeError("pynput is not available.")

    if not _lock.acquire(blocking=False):
        return False  # busy (execute or manual already running)

    kb = Controller()
    kb.press(Key.ctrl)
    time.sleep(ctrl_delay)

    _manual_keyboard = kb
    _manual_active = True
    _reset_manual_timer(timeout)
    return True


def manual_key(
    direction: str,
    timeout: float = _MANUAL_TIMEOUT_DEFAULT,
    key_hold: float = 0.05,
) -> bool:
    """Press one directional key while Ctrl is held. Resets inactivity timer.

    Args:
        direction: One of "up", "down", "left", "right".
        timeout: Inactivity seconds to reset the auto-release timer to.
        key_hold: Seconds to hold the key before releasing (default 50 ms).

    Returns False if manual mode is not active.
    """
    if not _manual_active or _manual_keyboard is None:
        return False

    if direction not in _KEY_MAP:
        raise ValueError(f"Invalid direction: {direction!r}")

    key = _KEY_MAP[direction]
    vk = _VK_CODES.get(direction, 0)
    t0 = time.time()
    log.debug("[KEYPRESS] 0.000s manual '%s' (VK=0x%02X) DOWN", direction, vk)
    _manual_keyboard.press(key)
    time.sleep(key_hold)
    _manual_keyboard.release(key)
    log.debug("[KEYPRESS] %.3fs manual '%s' (VK=0x%02X) UP", time.time() - t0, direction, vk)
    _reset_manual_timer(timeout)
    return True


def manual_stop() -> bool:
    """Release Ctrl and end manual mode. Returns False if not active."""
    global _manual_active, _manual_keyboard, _manual_timer

    if not _manual_active:
        return False

    if _manual_timer is not None:
        _manual_timer.cancel()
        _manual_timer = None

    if _manual_keyboard is not None:
        try:
            _manual_keyboard.release(Key.ctrl)
        except Exception:
            pass
        _manual_keyboard = None

    _manual_active = False
    try:
        _lock.release()
    except RuntimeError:
        pass
    return True


def is_manual_active() -> bool:
    """Return True if manual mode is currently holding Ctrl."""
    return _manual_active


def execute_stratagem(
    keys: list[str],
    key_delay_min_ms: float = 50,
    key_delay_max_ms: float = 80,
    ctrl_delay: float = 0.15,
    key_hold: float = 0.05,
    auto_click: bool = False,
    # Deprecated alias kept for backward compat (sets both min and max)
    key_delay: float | None = None,
) -> bool:
    """Press Ctrl, type directional key sequence, release Ctrl.

    Args:
        keys: List of directional inputs, e.g. ["up", "right", "down"].
        key_delay_min_ms: Minimum inter-key delay in ms (default 50).
        key_delay_max_ms: Maximum inter-key delay in ms (default 80). Equal to min = no randomness.
        ctrl_delay: Seconds to wait after pressing Ctrl before the first key (default 150 ms).
        key_hold: Seconds to hold each key before releasing (default 50 ms).
        auto_click: If True, clicks the left mouse button after Ctrl release
                    (auto-throw the stratagem marker).

    Returns:
        True on success.

    Raises:
        RuntimeError: If pynput is not available (WSL/non-Windows environment).
        ValueError: If keys list is empty or contains invalid directions.
        BlockingIOError: If another stratagem is currently being executed.
    """
    # Backward compat: key_delay (seconds) sets both min and max (no randomness)
    if key_delay is not None:
        key_delay_min_ms = key_delay * 1000
        key_delay_max_ms = key_delay * 1000

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

    log.debug(
        "[KEYPRESS] start sequence=%s key_hold=%.0fms delay=%g–%gms ctrl_delay=%.0fms",
        keys, key_hold * 1000, key_delay_min_ms, key_delay_max_ms, ctrl_delay * 1000,
    )

    try:
        keyboard = Controller()
        t0 = time.time()

        keyboard.press(Key.ctrl)
        log.debug("[KEYPRESS] %.3fs Ctrl DOWN", 0.0)
        time.sleep(ctrl_delay)

        for direction in keys:
            key = _KEY_MAP[direction]
            vk = _VK_CODES.get(direction, 0)
            log.debug("[KEYPRESS] %.3fs '%s' (VK=0x%02X) DOWN", time.time() - t0, direction, vk)
            keyboard.press(key)
            time.sleep(key_hold)
            keyboard.release(key)
            actual_ms = _random_delay(key_delay_min_ms, key_delay_max_ms)
            log.debug(
                "[KEYPRESS] %.3fs '%s' (VK=0x%02X) UP  delay=%.1fms (range: %.0f–%.0fms)",
                time.time() - t0, direction, vk, actual_ms, key_delay_min_ms, key_delay_max_ms,
            )

        keyboard.release(Key.ctrl)
        log.debug("[KEYPRESS] %.3fs Ctrl UP", time.time() - t0)

        if auto_click and MouseController is not None:
            time.sleep(0.05)
            mouse = MouseController()
            mouse.click(MouseButton.left)
            log.debug("[KEYPRESS] %.3fs LMB click (auto-throw)", time.time() - t0)

    finally:
        _lock.release()

    return True


def is_available() -> bool:
    """Return True if pynput is available and key simulation can be used."""
    return _PYNPUT_AVAILABLE
