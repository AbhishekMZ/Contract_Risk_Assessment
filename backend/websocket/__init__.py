# WebSocket package initialization
from .connection_manager import manager
from .events import EventType

__all__ = ["manager", "EventType"]
