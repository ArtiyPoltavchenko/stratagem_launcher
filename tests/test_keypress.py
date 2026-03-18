"""Tests for server/keypress.py — pynput is fully mocked."""

import threading
import pytest
from unittest.mock import MagicMock, call


@pytest.fixture(autouse=True)
def mock_pynput(monkeypatch):
    """Inject mock pynput.keyboard so keypress works without the real library."""
    # Mock Key (for Ctrl)
    mock_key = MagicMock()
    mock_key.ctrl = "CTRL"

    # Mock KeyCode.from_vk — returns a unique sentinel per VK code
    vk_sentinels: dict[int, str] = {}

    def fake_from_vk(vk: int):
        if vk not in vk_sentinels:
            vk_sentinels[vk] = f"VK_{vk:#04x}"
        return vk_sentinels[vk]

    mock_keycode = MagicMock()
    mock_keycode.from_vk.side_effect = fake_from_vk

    mock_controller_instance = MagicMock()
    mock_controller_cls = MagicMock(return_value=mock_controller_instance)

    import sys
    mock_keyboard_module = MagicMock()
    mock_keyboard_module.Controller = mock_controller_cls
    mock_keyboard_module.Key = mock_key
    mock_keyboard_module.KeyCode = mock_keycode

    pynput_mock = MagicMock()
    pynput_mock.keyboard = mock_keyboard_module
    monkeypatch.setitem(sys.modules, "pynput", pynput_mock)
    monkeypatch.setitem(sys.modules, "pynput.keyboard", mock_keyboard_module)

    import server.keypress as kp
    monkeypatch.setattr(kp, "_PYNPUT_AVAILABLE", True)
    monkeypatch.setattr(kp, "Controller", mock_controller_cls)
    monkeypatch.setattr(kp, "Key", mock_key)
    monkeypatch.setattr(kp, "KeyCode", mock_keycode)
    # Rebuild _KEY_MAP with the mocked KeyCode
    monkeypatch.setattr(kp, "_KEY_MAP", kp._build_key_map())

    yield mock_controller_instance, mock_key, vk_sentinels


@pytest.fixture(autouse=True)
def reset_lock():
    """Ensure the global lock is released and manual mode is reset between tests."""
    import server.keypress as kp
    kp._lock = threading.Lock()
    # Reset manual state
    if kp._manual_timer is not None:
        kp._manual_timer.cancel()
    kp._manual_active = False
    kp._manual_keyboard = None
    kp._manual_timer = None
    yield
    # Cleanup after test
    if kp._manual_timer is not None:
        kp._manual_timer.cancel()
    kp._manual_active = False
    kp._manual_keyboard = None
    kp._manual_timer = None
    if kp._lock.locked():
        kp._lock.release()


class TestExecuteStratagem:
    def test_returns_true_on_success(self, mock_pynput):
        from server.keypress import execute_stratagem
        assert execute_stratagem(["up", "right"], key_delay_min_ms=0, key_delay_max_ms=0, ctrl_delay=0) is True

    def test_presses_ctrl_first(self, mock_pynput):
        controller, key, _ = mock_pynput
        from server.keypress import execute_stratagem
        execute_stratagem(["up"], key_delay_min_ms=0, key_delay_max_ms=0, ctrl_delay=0)
        assert controller.press.call_args_list[0] == call(key.ctrl)

    def test_releases_ctrl_last(self, mock_pynput):
        controller, key, _ = mock_pynput
        from server.keypress import execute_stratagem
        execute_stratagem(["up"], key_delay_min_ms=0, key_delay_max_ms=0, ctrl_delay=0)
        assert controller.release.call_args_list[-1] == call(key.ctrl)

    def test_correct_vk_sequence(self, mock_pynput):
        """Keys are sent as VK codes (not raw chars) in the correct order."""
        controller, key, vk_sentinels = mock_pynput
        from server.keypress import execute_stratagem, _KEY_MAP
        execute_stratagem(["up", "down", "left", "right"], key_delay_min_ms=0, key_delay_max_ms=0, ctrl_delay=0)

        pressed = [c.args[0] for c in controller.press.call_args_list]
        # First press is Ctrl, then up/down/left/right VK codes
        assert pressed[0] == key.ctrl
        assert pressed[1] == _KEY_MAP["up"]
        assert pressed[2] == _KEY_MAP["down"]
        assert pressed[3] == _KEY_MAP["left"]
        assert pressed[4] == _KEY_MAP["right"]

    def test_vk_codes_not_raw_chars(self, mock_pynput):
        """Verify keys are NOT raw 'w','a','s','d' strings — must be VK objects."""
        controller, key, _ = mock_pynput
        from server.keypress import execute_stratagem
        execute_stratagem(["up", "down", "left", "right"], key_delay_min_ms=0, key_delay_max_ms=0, ctrl_delay=0)
        pressed = [c.args[0] for c in controller.press.call_args_list[1:]]  # skip Ctrl
        for k in pressed:
            assert k not in ("w", "a", "s", "d"), f"Raw char sent instead of VK code: {k!r}"

    def test_raises_on_empty_keys(self, mock_pynput):
        from server.keypress import execute_stratagem
        with pytest.raises(ValueError, match="empty"):
            execute_stratagem([])

    def test_raises_on_invalid_direction(self, mock_pynput):
        from server.keypress import execute_stratagem
        with pytest.raises(ValueError, match="Invalid key directions"):
            execute_stratagem(["up", "invalid"])

    def test_raises_when_locked(self, mock_pynput):
        import server.keypress as kp
        from server.keypress import execute_stratagem
        kp._lock.acquire()
        try:
            with pytest.raises(BlockingIOError, match="Another stratagem"):
                execute_stratagem(["up"], key_delay_min_ms=0, key_delay_max_ms=0, ctrl_delay=0)
        finally:
            kp._lock.release()

    def test_lock_released_after_success(self, mock_pynput):
        import server.keypress as kp
        from server.keypress import execute_stratagem
        execute_stratagem(["up"], key_delay_min_ms=0, key_delay_max_ms=0, ctrl_delay=0)
        assert not kp._lock.locked()

    def test_lock_released_after_error(self, mock_pynput):
        import server.keypress as kp
        from server.keypress import execute_stratagem
        with pytest.raises(ValueError):
            execute_stratagem(["bad_direction"], key_delay_min_ms=0, key_delay_max_ms=0, ctrl_delay=0)
        assert not kp._lock.locked()

    def test_key_hold_between_press_and_release(self, mock_pynput):
        """key_hold sleep fires between press() and release() for each direction key."""
        from unittest.mock import patch
        import server.keypress as kp
        controller, key, _ = mock_pynput

        events: list = []
        controller.press.side_effect = lambda k: events.append(("press", k))
        controller.release.side_effect = lambda k: events.append(("release", k))

        with patch("time.sleep") as mock_sleep:
            mock_sleep.side_effect = lambda t: events.append(("sleep", t))
            kp.execute_stratagem(["up"], key_delay_min_ms=60, key_delay_max_ms=60, ctrl_delay=0.0, key_hold=0.04)

        up_key = kp._KEY_MAP["up"]
        press_idx = next(i for i, e in enumerate(events) if e == ("press", up_key))
        release_idx = next(i for i, e in enumerate(events) if e == ("release", up_key))
        between = events[press_idx + 1 : release_idx]
        assert ("sleep", 0.04) in between, f"key_hold sleep not found between press/release: {between}"

    def test_key_delay_after_release(self, mock_pynput):
        """key_delay sleep fires after release() and before the next press (or Ctrl UP)."""
        from unittest.mock import patch
        import server.keypress as kp
        controller, key, _ = mock_pynput

        events: list = []
        controller.press.side_effect = lambda k: events.append(("press", k))
        controller.release.side_effect = lambda k: events.append(("release", k))

        with patch("time.sleep") as mock_sleep:
            mock_sleep.side_effect = lambda t: events.append(("sleep", t))
            kp.execute_stratagem(["up"], key_delay_min_ms=60, key_delay_max_ms=60, ctrl_delay=0.0, key_hold=0.0)

        up_key = kp._KEY_MAP["up"]
        release_idx = next(i for i, e in enumerate(events) if e == ("release", up_key))
        after = events[release_idx + 1 :]
        assert ("sleep", 0.06) in after, f"key_delay sleep not found after release: {after}"


class TestIsAvailable:
    def test_returns_bool(self):
        from server.keypress import is_available
        assert isinstance(is_available(), bool)

    def test_true_when_pynput_mocked(self, mock_pynput):
        import server.keypress as kp
        assert kp._PYNPUT_AVAILABLE is True


class TestManualMode:
    def test_start_returns_true(self, mock_pynput):
        from server.keypress import manual_start, manual_stop
        assert manual_start(ctrl_delay=0, timeout=5) is True
        manual_stop()

    def test_start_presses_ctrl(self, mock_pynput):
        controller, key, _ = mock_pynput
        from server.keypress import manual_start, manual_stop
        manual_start(ctrl_delay=0, timeout=5)
        assert call(key.ctrl) in controller.press.call_args_list
        manual_stop()

    def test_start_returns_false_when_locked(self, mock_pynput):
        import server.keypress as kp
        from server.keypress import manual_start
        kp._lock.acquire()
        assert manual_start(ctrl_delay=0, timeout=5) is False

    def test_execute_blocked_during_manual(self, mock_pynput):
        from server.keypress import manual_start, execute_stratagem, manual_stop
        manual_start(ctrl_delay=0, timeout=5)
        with pytest.raises(BlockingIOError):
            execute_stratagem(["up"], key_delay_min_ms=0, key_delay_max_ms=0, ctrl_delay=0)
        manual_stop()

    def test_manual_key_sends_vk(self, mock_pynput):
        controller, key, _ = mock_pynput
        from server.keypress import manual_start, manual_key, manual_stop, _KEY_MAP
        manual_start(ctrl_delay=0, timeout=5)
        manual_key("up")
        pressed = [c.args[0] for c in controller.press.call_args_list]
        assert _KEY_MAP["up"] in pressed
        manual_stop()

    def test_manual_key_all_directions(self, mock_pynput):
        controller, key, _ = mock_pynput
        from server.keypress import manual_start, manual_key, manual_stop, _KEY_MAP
        manual_start(ctrl_delay=0, timeout=5)
        for d in ("up", "down", "left", "right"):
            assert manual_key(d) is True
        manual_stop()

    def test_manual_key_invalid_direction(self, mock_pynput):
        from server.keypress import manual_start, manual_key, manual_stop
        manual_start(ctrl_delay=0, timeout=5)
        with pytest.raises(ValueError, match="Invalid direction"):
            manual_key("diagonal")
        manual_stop()

    def test_manual_key_returns_false_when_not_active(self, mock_pynput):
        from server.keypress import manual_key
        assert manual_key("up") is False

    def test_manual_key_hold_between_press_and_release(self, mock_pynput):
        """manual_key applies key_hold sleep between press() and release()."""
        from unittest.mock import patch
        import server.keypress as kp
        from server.keypress import manual_start, manual_key, manual_stop
        controller, key, _ = mock_pynput

        events: list = []
        controller.press.side_effect = lambda k: events.append(("press", k))
        controller.release.side_effect = lambda k: events.append(("release", k))

        manual_start(ctrl_delay=0, timeout=5)
        with patch("time.sleep") as mock_sleep:
            mock_sleep.side_effect = lambda t: events.append(("sleep", t))
            manual_key("up", key_hold=0.04)

        up_key = kp._KEY_MAP["up"]
        press_idx = next(i for i, e in enumerate(events) if e == ("press", up_key))
        release_idx = next(i for i, e in enumerate(events) if e == ("release", up_key))
        between = events[press_idx + 1 : release_idx]
        assert ("sleep", 0.04) in between, f"key_hold not found between press/release: {between}"
        manual_stop()

    def test_stop_releases_ctrl(self, mock_pynput):
        controller, key, _ = mock_pynput
        from server.keypress import manual_start, manual_stop
        manual_start(ctrl_delay=0, timeout=5)
        manual_stop()
        assert call(key.ctrl) in controller.release.call_args_list

    def test_stop_releases_lock(self, mock_pynput):
        import server.keypress as kp
        from server.keypress import manual_start, manual_stop
        manual_start(ctrl_delay=0, timeout=5)
        assert kp._lock.locked()
        manual_stop()
        assert not kp._lock.locked()

    def test_stop_returns_false_when_not_active(self, mock_pynput):
        from server.keypress import manual_stop
        assert manual_stop() is False

    def test_is_manual_active(self, mock_pynput):
        from server.keypress import manual_start, manual_stop, is_manual_active
        assert not is_manual_active()
        manual_start(ctrl_delay=0, timeout=5)
        assert is_manual_active()
        manual_stop()
        assert not is_manual_active()

    def test_auto_timeout_releases_ctrl(self, mock_pynput):
        controller, key, _ = mock_pynput
        from server.keypress import manual_start, is_manual_active
        manual_start(ctrl_delay=0, timeout=0.05)
        import time; time.sleep(0.15)
        assert not is_manual_active()
        assert call(key.ctrl) in controller.release.call_args_list
