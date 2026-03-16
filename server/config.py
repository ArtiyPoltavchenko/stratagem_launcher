"""Server configuration with defaults, overridable via CLI args or environment variables."""

from dataclasses import dataclass


@dataclass
class Config:
    key_delay_ms: int = 50
    ctrl_hold_delay_ms: int = 30
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


# Global config instance (can be replaced in app.py after parsing CLI args)
config = Config()
