"""
FrankerFaceZ emote provider implementation.
"""
import logging
import requests
from typing import Dict, Any, Optional
from providers.provider_base import EmoteProvider

logger = logging.getLogger("TwitchTracker.FFZProvider")


class FFZEmoteProvider(EmoteProvider):
    """Provider for FrankerFaceZ emotes."""
    name = "FFZ"
    
    def __init__(self):
        self.global_emotes = {}
        self.channel_emotes = {}
    
    async def fetch_emotes(self, channel_name=None) -> Dict[str, Any]:
        """
        Fetch FFZ emotes (global and channel-specific).
        
        Args:
            channel_name: Optional Twitch channel name for channel-specific emotes
            
        Returns:
            Dict[str, Any]: Dictionary of emotes with metadata
        """
        try:
            # Fetch global emotes
            global_url = "https://api.frankerfacez.com/v1/set/global"
            global_response = requests.get(global_url)
            global_response.raise_for_status()
            
            # Process global emotes
            global_data = global_response.json()
            for set_id, emote_set in global_data.get('sets', {}).items():
                for emote in emote_set.get('emoticons', []):
                    urls = emote.get('urls', {})
                    # Get highest quality available
                    best_url = urls.get('4') or urls.get('2') or urls.get('1')
                    if best_url:
                        self.global_emotes[emote['name']] = {
                            'id': str(emote['id']),
                            'url': f"https:{best_url}",
                            'type': 'ffz'
                        }
            
            # Fetch channel emotes if channel_name is provided
            if channel_name:
                channel_url = f"https://api.frankerfacez.com/v1/room/{channel_name}"
                channel_response = requests.get(channel_url)
                if channel_response.status_code == 200:
                    channel_data = channel_response.json()
                    for set_id, emote_set in channel_data.get('sets', {}).items():
                        for emote in emote_set.get('emoticons', []):
                            urls = emote.get('urls', {})
                            best_url = urls.get('4') or urls.get('2') or urls.get('1')
                            if best_url:
                                self.channel_emotes[emote['name']] = {
                                    'id': str(emote['id']),
                                    'url': f"https:{best_url}",
                                    'type': 'ffz'
                                }
            
            # Combine both sets
            combined = {**self.global_emotes, **self.channel_emotes}
            logger.info(f"Loaded {len(combined)} FFZ emotes")
            return combined
            
        except Exception as e:
            logger.error(f"Error fetching FFZ emotes: {e}")
            return {}
    
    def get_emote_url(self, emote_id: str) -> Optional[str]:
        """
        Get URL for FFZ emote (using pre-stored URL).
        
        Args:
            emote_id: ID of the FFZ emote
            
        Returns:
            Optional[str]: URL of the FFZ emote or None if not found
        """
        # For FFZ, we store the full URL since it varies by emote
        for emotes in [self.global_emotes, self.channel_emotes]:
            for name, data in emotes.items():
                if data['id'] == emote_id:
                    return data['url']
        return None