"""Tests for server/keypress.py — pynput is fully mocked."""

import threading
import pytest
from unittest.mock import MagicMock, patch, call


# Patch pynput before importing keypress so the module sees it as available
@pytest.fixture(autouse=True)
def mock_pynput(monkeypatch):
    """Inject mock pynput.keyboard so keypress works without the real library."""
    mock_key = MagicMock()
    mock_key.ctrl = "CTRL"

    mock_controller_instance = MagicMock()
    mock_controller_cls = MagicMock(return_value=mock_controller_instance)

    mock_keyboard_module = MagicMock()
    mock_keyboard_module.Controller = mock_controller_cls
    mock_keyboard_module.Key = mock_key

    import sys
    pynput_mock = MagicMock()
    pynput_mock.keyboard = mock_keyboard_module
    monkeypatch.setitem(sys.modules, "pynput", pynput_mock)
    monkeypatch.setitem(sys.modules, "pynput.keyboard", mock_keyboard_module)

    # Force keypress to reload with mocked pynput
    import importlib
    import server.keypress as kp
    monkeypatch.setattr(kp, "_PYNPUT_AVAILABLE", True)
    monkeypatch.setattr(kp, "Controller", mock_controller_cls)
    monkeypatch.setattr(kp, "Key", mock_key)

    yield mock_controller_instance, mock_key


@pytest.fixture(autouse=True)
def reset_lock():
    """Ensure the global lock is released between tests."""
    import server.keypress as kp
    # Replace lock with a fresh one before each test
    kp._lock = threading.Lock()
    yield


class TestExecuteStratagem:
    def test_returns_true_on_success(self, mock_pynput):
        from server.keypress import execute_stratagem
        result = execute_stratagem(["up", "right"], key_delay=0, ctrl_delay=0)
        assert result is True

    def test_presses_ctrl_first(self, mock_pynput):
        controller, key = mock_pynput
        from server.keypress import execute_stratagem
        execute_stratagem(["up"], key_delay=0, ctrl_delay=0)
        first_call = controller.press.call_args_list[0]
        assert first_call == call(key.ctrl)

    def test_releases_ctrl_last(self, mock_pynput):
        controller, key = mock_pynput
        from server.keypress import execute_stratagem
        execute_stratagem(["up"], key_delay=0, ctrl_delay=0)
        last_call = controller.release.call_args_list[-1]
        assert last_call == call(key.ctrl)

    def test_correct_key_sequence(self, mock_pynput):
        controller, key = mock_pynput
        from server.keypress import execute_stratagem
        execute_stratagem(["up", "down", "left", "right"], key_delay=0, ctrl_delay=0)

        pressed = [c.args[0] for c in controller.press.call_args_list]
        # First press is Ctrl, then w, s, a, d
        assert pressed == [key.ctrl, "w", "s", "a", "d"]

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
