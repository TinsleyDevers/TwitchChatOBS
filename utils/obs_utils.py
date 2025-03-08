"""
OBS WebSocket utility functions for the Twitch Tracker application.
"""
import logging
from typing import Optional
from obswebsocket import obsws, requests as obs_requests

logger = logging.getLogger("TwitchTracker.OBSUtils")


class OBSManager:
    """OBS WebSocket manager."""
    
    def __init__(self, host: str = "localhost", port: int = 4444, password: str = ""):
        """
        Initialize the OBS WebSocket manager.
        
        Args:
            host: OBS WebSocket host
            port: OBS WebSocket port
            password: OBS WebSocket password
        """
        self.host = host
        self.port = port
        self.password = password
        self.obs = None
        self.connected = False
    
    def connect(self) -> bool:
        """
        Connect to OBS WebSocket.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.obs = obsws(self.host, self.port, self.password)
            self.obs.connect()
            self.connected = True
            logger.info("Connected to OBS WebSocket")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to OBS: {e}")
            self.obs = None
            self.connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from OBS WebSocket."""
        if self.obs and self.connected:
            try:
                self.obs.disconnect()
                logger.info("Disconnected from OBS WebSocket")
            except Exception as e:
                logger.error(f"Error disconnecting from OBS: {e}")
            finally:
                self.obs = None
                self.connected = False
    
    def update_text_source(self, source_name: str, text: str) -> bool:
        """
        Update the text in an OBS text source.
        
        Args:
            source_name: Name of the OBS text source
            text: New text content
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.obs or not self.connected:
            logger.warning("Cannot update OBS text source: not connected")
            return False
        
        try:
            self.obs.call(obs_requests.SetTextGDIPlusProperties(
                source=source_name,
                text=text
            ))
            return True
            
        except Exception as e:
            logger.error(f"Failed to update OBS text source: {e}")
            # Try to reconnect
            self.connect()
            return False