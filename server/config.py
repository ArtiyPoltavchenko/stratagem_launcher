"""Server configuration with defaults, overridable via CLI args or environment variables."""

from dataclasses import dataclass


@dataclass
class Config:
    key_delay_ms: int = 80         # inter-key pause after release (ms)
    ctrl_hold_delay_ms: int = 150  # pause after Ctrl press before first key (ms)
    key_hold_ms: int = 50          # how long to hold each key before releasing (ms)
    auto_click: bool = False       # click LMB after stratagem to auto-throw marker
    host: str = "127.0.0.1"
    port: int = 5000
    debug: bool = False

    @property
    def key_delay(self) -> float:
        """Key delay in seconds."""
        return self.key_delay_ms / 1000.0

    @property
    def ctrl_hold_delay(self) -> float:
        """Ctrl hold delay in seconds."""
        return self.ctrl_hold_delay_ms / 1000.0

    @property
    def key_hold(self) -> float:
        """Key hold duration in seconds."""
        return self.key_hold_ms / 1000.0


# Global config instance (can be replaced in app.py after parsing CLI args)
config = Config()
