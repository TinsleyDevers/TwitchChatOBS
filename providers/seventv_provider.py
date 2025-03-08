"""
7TV emote provider implementation.
"""
import logging
import requests
from typing import Dict, Any, Optional
from providers.provider_base import EmoteProvider

logger = logging.getLogger("TwitchTracker.SevenTVProvider")


class SevenTVEmoteProvider(EmoteProvider):
    """Provider for 7TV emotes."""
    name = "7TV"
    
    def __init__(self):
        self.global_emotes = {}
        self.channel_emotes = {}
    
    async def fetch_emotes(self, channel_id=None) -> Dict[str, Any]:
        """
        Fetch 7TV emotes (global and channel-specific).
        
        Args:
            channel_id: Optional Twitch channel ID for channel-specific emotes
            
        Returns:
            Dict[str, Any]: Dictionary of emotes with metadata
        """
        try:
            # Fetch global emotes
            global_url = "https://api.7tv.app/v2/emotes/global"
            global_response = requests.get(global_url)
            global_response.raise_for_status()
            
            # Process global emotes
            for emote in global_response.json():
                self.global_emotes[emote['name']] = {
                    'id': emote['id'],
                    'type': '7tv'
                }
            
            # Fetch channel emotes if channel_id is provided
            if channel_id:
                channel_url = f"https://api.7tv.app/v2/users/{channel_id}/emotes"
                channel_response = requests.get(channel_url)
                if channel_response.status_code == 200:
                    for emote in channel_response.json():
                        self.channel_emotes[emote['name']] = {
                            'id': emote['id'],
                            'type': '7tv'
                        }
            
            # Combine both sets
            combined = {**self.global_emotes, **self.channel_emotes}
            logger.info(f"Loaded {len(combined)} 7TV emotes")
            return combined
            
        except Exception as e:
            logger.error(f"Error fetching 7TV emotes: {e}")
            return {}
    
    def get_emote_url(self, emote_id: str) -> str:
        """
        Get URL for 7TV emote.
        
        Args:
            emote_id: ID of the 7TV emote
            
        Returns:
            str: URL of the 7TV emote
        """
        return f"https://cdn.7tv.app/emote/{emote_id}/3x"