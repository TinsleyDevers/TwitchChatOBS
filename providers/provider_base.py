"""
Base class for emote providers.
"""
from typing import Dict, Optional, Any


class EmoteProvider:
    """Base class for emote providers."""
    name = "Base"
    
    async def fetch_emotes(self) -> Dict[str, Any]:
        """
        Fetch emotes from provider.
        
        Returns:
            Dict[str, Any]: Dictionary of emotes with metadata
        """
        return {}
    
    def get_emote_url(self, emote_id: str) -> Optional[str]:
        """
        Get URL for emote.
        
        Args:
            emote_id: ID of the emote
            
        Returns:
            Optional[str]: URL of the emote or None if not found
        """
        return None