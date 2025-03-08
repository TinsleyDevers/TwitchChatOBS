"""
BetterTTV emote provider implementation.
"""
import logging
import requests
from typing import Dict, Any, Optional
from providers.provider_base import EmoteProvider

logger = logging.getLogger("TwitchTracker.BTTVProvider")


class BTTVEmoteProvider(EmoteProvider):
    """Provider for BetterTTV emotes."""
    name = "BTTV"
    
    def __init__(self):
        self.global_emotes = {}
        self.channel_emotes = {}
        
    async def fetch_emotes(self, channel_id=None) -> Dict[str, Any]:
        """
        Fetch BTTV emotes (global and channel-specific).
        
        Args:
            channel_id: Optional Twitch channel ID for channel-specific emotes
            
        Returns:
            Dict[str, Any]: Dictionary of emotes with metadata
        """
        try:
            # Fetch global emotes
            global_url = "https://api.betterttv.net/3/cached/emotes/global"
            global_response = requests.get(global_url)
            global_response.raise_for_status()
            
            # Process global emotes
            for emote in global_response.json():
                self.global_emotes[emote['code']] = {
                    'id': emote['id'],
                    'type': 'bttv'
                }
                
            # Fetch channel emotes if channel_id is provided
            if channel_id:
                channel_url = f"https://api.betterttv.net/3/cached/users/twitch/{channel_id}"
                channel_response = requests.get(channel_url)
                if channel_response.status_code == 200:
                    data = channel_response.json()
                    
                    # Process channel emotes
                    for emote in data.get('channelEmotes', []) + data.get('sharedEmotes', []):
                        self.channel_emotes[emote['code']] = {
                            'id': emote['id'],
                            'type': 'bttv'
                        }
            
            # Combine both sets
            combined = {**self.global_emotes, **self.channel_emotes}
            logger.info(f"Loaded {len(combined)} BTTV emotes")
            return combined
            
        except Exception as e:
            logger.error(f"Error fetching BTTV emotes: {e}")
            return {}
    
    def get_emote_url(self, emote_id: str) -> str:
        """
        Get URL for BTTV emote.
        
        Args:
            emote_id: ID of the BTTV emote
            
        Returns:
            str: URL of the BTTV emote
        """
        return f"https://cdn.betterttv.net/emote/{emote_id}/3x"