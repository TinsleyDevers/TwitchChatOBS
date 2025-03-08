"""
Data models for the Twitch Tracker application.
"""
from dataclasses import dataclass, field
from typing import Optional, Set


@dataclass
class EmoteConfig:
    """Configuration for an emote or word."""
    is_emote: bool
    custom_audio: Optional[str] = None
    color: str = "#FFFFFF"
    font: str = "Arial"
    size: int = 24
    display_time: int = 5
    combo_timeout: int = 10
    show_in_overlay: bool = True
    animation: str = "bounce"  # Animation style for the emote


@dataclass
class ComboItem:
    """Represents an active combo item."""
    text: str
    combo: int
    is_emote: bool
    emote_id: Optional[str] = None
    emote_url: Optional[str] = None
    expires: float = 0
    contributors: Set[str] = field(default_factory=set)