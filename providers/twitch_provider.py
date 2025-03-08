"""
Twitch emote provider implementation.
"""
from typing import Optional
from providers.provider_base import EmoteProvider


class TwitchEmoteProvider(EmoteProvider):
    """Provider for Twitch emotes."""
    name = "Twitch"
    
    def get_emote_url(self, emote_id: str) -> str:
        """
        Get URL for Twitch emote.
        
        Args:
            emote_id: ID of the Twitch emote
            
        Returns:
            str: URL of the Twitch emote
        """
        return f"https://static-cdn.jtvnw.net/emoticons/v2/{emote_id}/default/dark/3.0"