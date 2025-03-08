"""
Audio management for the Twitch Tracker application.
"""
import os
import logging
import threading
from typing import Optional

logger = logging.getLogger("TwitchTracker.AudioManager")


class AudioManager:
    """Manager for audio playback and text-to-speech functionality."""
    
    def __init__(self):
        """Initialize the AudioManager."""
        self.tts_enabled = True
        self.tts_rate = 150
        self.tts_volume = 0.8
        self.tts_engine = None
        self.pygame_initialized = False
        
        # Initialize the audio systems
        self._init_audio()
    
    def _init_audio(self):
        """Initialize audio playback and TTS systems."""
        try:
            # Initialize pygame for audio playback
            import pygame
            pygame.mixer.init()
            self.pygame_initialized = True
            logger.info("Pygame audio initialized")
        except Exception as e:
            logger.error(f"Failed to initialize pygame: {e}")
        
        try:
            # Initialize TTS engine
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', self.tts_rate)
            self.tts_engine.setProperty('volume', self.tts_volume)
            logger.info("TTS engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            self.tts_engine = None
    
    def configure_tts(self, enabled: bool = True, rate: int = 150, volume: float = 0.8) -> bool:
        """
        Configure TTS settings.
        
        Args:
            enabled: Whether TTS is enabled
            rate: Speaking rate (words per minute)
            volume: Volume level (0.0-1.0)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.tts_enabled = enabled
            self.tts_rate = rate
            self.tts_volume = volume
            
            if self.tts_engine:
                self.tts_engine.setProperty('rate', rate)
                self.tts_engine.setProperty('volume', volume)
                logger.info(f"TTS configured: enabled={enabled}, rate={rate}, volume={volume}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Failed to configure TTS: {e}")
            return False
    
    def play_audio_file(self, file_path: str) -> bool:
        """
        Play an audio file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(file_path):
            logger.warning(f"Audio file not found: {file_path}")
            return False
            
        if not self.pygame_initialized:
            logger.warning("Cannot play audio: pygame not initialized")
            return False
            
        try:
            # Load and play in a separate thread to avoid blocking
            def play():
                try:
                    import pygame
                    sound = pygame.mixer.Sound(file_path)
                    sound.play()
                except Exception as e:
                    logger.error(f"Error playing audio in thread: {e}")
            
            threading.Thread(target=play, daemon=True).start()
            return True
        except Exception as e:
            logger.error(f"Failed to play audio {file_path}: {e}")
            return False
    
    def speak_text(self, text: str) -> bool:
      """
      Speak text using TTS.
      
      Args:
          text: Text to speak
          
      Returns:
          bool: True if successful, False otherwise
      """
      if not self.tts_enabled or not self.tts_engine:
          logger.warning(f"TTS not enabled or engine not available. Enabled: {self.tts_enabled}")
          return False
      
      try:
          # Execute TTS in a separate thread to avoid blocking
          def tts_thread():
              try:
                  logger.info(f"TTS thread starting for text: '{text}'")
                  self.tts_engine.say(text)
                  self.tts_engine.runAndWait()
                  logger.info("TTS completed successfully")
              except Exception as e:
                  logger.error(f"Error in TTS thread: {e}")
          
          thread = threading.Thread(target=tts_thread, daemon=True)
          thread.start()
          return True
      except Exception as e:
          logger.error(f"TTS error: {e}")
          return False