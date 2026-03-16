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
    """Ensure the global lock is released between tests."""
    import server.keypress as kp
    kp._lock = threading.Lock()
    yield


class TestExecuteStratagem:
    def test_returns_true_on_success(self, mock_pynput):
        from server.keypress import execute_stratagem
        assert execute_stratagem(["up", "right"], key_delay=0, ctrl_delay=0) is True

    def test_presses_ctrl_first(self, mock_pynput):
        controller, key, _ = mock_pynput
        from server.keypress import execute_stratagem
        execute_stratagem(["up"], key_delay=0, ctrl_delay=0)
        assert controller.press.call_args_list[0] == call(key.ctrl)

    def test_releases_ctrl_last(self, mock_pynput):
        controller, key, _ = mock_pynput
        from server.keypress import execute_stratagem
        execute_stratagem(["up"], key_delay=0, ctrl_delay=0)
        assert controller.release.call_args_list[-1] == call(key.ctrl)

    def test_correct_vk_sequence(self, mock_pynput):
        """Keys are sent as VK codes (not raw chars) in the correct order."""
        controller, key, vk_sentinels = mock_pynput
        from server.keypress import execute_stratagem, _KEY_MAP
        execute_stratagem(["up", "down", "left", "right"], key_delay=0, ctrl_delay=0)

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
        execute_stratagem(["up", "down", "left", "right"], key_delay=0, ctrl_delay=0)
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
                execute_stratagem(["up"], key_delay=0, ctrl_delay=0)
        finally:
            kp._lock.release()

    def test_lock_released_after_success(self, mock_pynput):
        import server.keypress as kp
        from server.keypress import execute_stratagem
        execute_stratagem(["up"], key_delay=0, ctrl_delay=0)
        assert not kp._lock.locked()

    def test_lock_released_after_error(self, mock_pynput):
        import server.keypress as kp
        from server.keypress import execute_stratagem
        with pytest.raises(ValueError):
            execute_stratagem(["bad_direction"], key_delay=0, ctrl_delay=0)
        assert not kp._lock.locked()


class TestIsAvailable:
    def test_returns_bool(self):
        from server.keypress import is_available
        assert isinstance(is_available(), bool)

    def test_true_when_pynput_mocked(self, mock_pynput):
        import server.keypress as kp
        assert kp._PYNPUT_AVAILABLE is True
