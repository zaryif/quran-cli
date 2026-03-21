"""
connectors/base.py — Abstract connector interface.
All notification channels implement this.
"""
from __future__ import annotations
from abc import ABC, abstractmethod


class BaseConnector(ABC):
    name: str = "base"

    @abstractmethod
    def send(self, title: str, body: str, **kwargs) -> bool:
        """Send a notification. Returns True on success."""

    @abstractmethod
    def test(self) -> bool:
        """Send a test message."""

    @abstractmethod
    def setup(self) -> dict:
        """Interactive setup wizard. Returns config dict."""

    @abstractmethod
    def is_configured(self, cfg: dict) -> bool:
        """Check if connector is properly configured."""
