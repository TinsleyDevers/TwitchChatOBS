"""
Main Twitch Tracker class.
"""
import os
import re
import time
import socket
import asyncio
import threading
import logging
import configparser
import json
from queue import Queue, Empty
from typing import Dict, Set, List, Tuple, Optional, Any
from collections import Counter

# Import core modules
from core.data_models import EmoteConfig, ComboItem
from core.combo_manager import ComboManager
from core.overlay_manager import OverlayManager

# Import providers
from providers import (
    TwitchEmoteProvider,
    BTTVEmoteProvider,
    FFZEmoteProvider,
    SevenTVEmoteProvider
)

# Import utilities
from utils.audio import AudioManager
from utils.obs_utils import OBSManager
from utils.file_utils import (
    ensure_directory,
    write_json_file,
    read_json_file,
    load_text_file_as_set,
    save_set_to_text_file
)

logger = logging.getLogger("TwitchTracker")


class TwitchTracker:
    """
    Main Twitch Tracker class.
    Handles Twitch chat connection, emote tracking, and integrations.
    """
    
    def __init__(self, config_path: str = "config.ini"):
        """
        Initialize the Twitch Tracker.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # Set up base directories
        self.base_dir = os.path.dirname(os.path.abspath(config_path))
        self.emotes_dir = os.path.join(self.base_dir, 'emotes')
        ensure_directory(self.emotes_dir)
        
        # Ensure static directory exists
        static_dir = os.path.join(self.base_dir, 'static')
        ensure_directory(static_dir)
        
        # Ensure static/emotes directory exists
        static_emotes_dir = os.path.join(static_dir, 'emotes')
        ensure_directory(static_emotes_dir)
        
        # Twitch connection settings
        self.server = 'irc.chat.twitch.tv'
        self.port = 6667
        self.nickname = self.config['Twitch']['nickname']
        self.token = self.config['Twitch']['token']
        self.channel = self.config['Twitch']['channel']
        self.channel_id = self.config.get('Twitch', 'channel_id', fallback='')
        
        # Combo settings
        self.default_combo_timeout = int(self.config.get('General', 'default_combo_timeout', fallback='10'))
        self.default_display_time = int(self.config.get('General', 'default_display_time', fallback='5'))
        self.allow_multiple_from_user = self.config.getboolean('General', 'allow_multiple_from_user', fallback=True)
        
        # Word processing settings
        self.min_word_length = int(self.config.get('General', 'min_word_length', fallback='2'))
        self.max_words_per_message = int(self.config.get('General', 'max_words_per_message', fallback='1'))
        
        # Load emotes and configurations
        self.known_emotes = self._load_known_emotes()
        self.emote_configs = self._load_emote_configs()
        
        # Initialize components
        self._init_components()
        
        # Socket and threading
        self.sock = None
        self.running = False
        self.chat_thread = None
        self.processing_thread = None
        
        # Initialization complete
        logger.info("TwitchTracker initialized")
    
    def _load_config(self) -> configparser.ConfigParser:
        """
        Load configuration or create default if not exists.
        
        Returns:
            configparser.ConfigParser: Loaded configuration
        """
        config = configparser.ConfigParser()
        
        if os.path.exists(self.config_path):
            config.read(self.config_path)
        else:
            # Create default config
            config['Twitch'] = {
                'nickname': 'your_bot_username',
                'token': 'oauth:your_token_here',
                'channel': 'your_channel',
                'channel_id': ''
            }
            
            config['OBS'] = {
                'host': 'localhost',
                'port': '4444',
                'password': 'your_password_here',
                'text_source': 'ChatTracker'
            }
            
            config['TTS'] = {
                'enabled': 'true',
                'rate': '150',
                'volume': '0.8'
            }
            
            config['General'] = {
                'default_combo_timeout': '10',
                'default_display_time': '5',
                'allow_multiple_from_user': 'true',
                'min_word_length': '2',
                'max_words_per_message': '1',
                'use_local_emotes': 'true'
            }
            
            config['UI'] = {
                'theme': 'dark',
                'accent_color': '#5a32a8'
            }
            
            config['Overlay'] = {
                'position': 'bottom-left',
                'scale': '1.0',
                'font': 'Arial'
            }
            
            with open(self.config_path, 'w') as configfile:
                config.write(configfile)
            
            logger.info(f"Created default config at {self.config_path}")
        
        return config
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)
        logger.info("Configuration saved")
    
    def _load_known_emotes(self) -> Set[str]:
        """
        Load known emotes from file.
        
        Returns:
            Set[str]: Set of known emote names
        """
        emotes_path = os.path.join(self.base_dir, 'emotes.txt')
        emotes = load_text_file_as_set(emotes_path)
        
        if not emotes:
            # Create default emotes file
            emotes = {"OMEGALUL", "Kappa", "PogChamp"}
            save_set_to_text_file(
                emotes_path, 
                emotes,
                "# Add one emote per line"
            )
            logger.info(f"Created default emotes file at {emotes_path}")
        
        return emotes
    
    def save_known_emotes(self) -> None:
        """Save known emotes to file."""
        emotes_path = os.path.join(self.base_dir, 'emotes.txt')
        save_set_to_text_file(
            emotes_path, 
            self.known_emotes,
            "# Add one emote per line"
        )
        logger.info("Emotes list saved")
    
    def _load_emote_configs(self) -> Dict[str, EmoteConfig]:
        """
        Load emote and word configurations.
        
        Returns:
            Dict[str, EmoteConfig]: Dictionary of emote/word configurations
        """
        configs = {}
        config_path = os.path.join(self.base_dir, 'emote_configs.json')
        
        data = read_json_file(config_path)
        if data:
            try:
                for key, cfg in data.items():
                    configs[key] = EmoteConfig(
                        is_emote=cfg.get('is_emote', key in self.known_emotes),
                        custom_audio=cfg.get('custom_audio'),
                        color=cfg.get('color', "#FFFFFF"),
                        font=cfg.get('font', "Arial"),
                        size=cfg.get('size', 24),
                        display_time=cfg.get('display_time', 5),
                        combo_timeout=cfg.get('combo_timeout', 10),
                        show_in_overlay=cfg.get('show_in_overlay', True),
                        animation=cfg.get('animation', 'bounce')
                    )
            except Exception as e:
                logger.error(f"Error loading emote configs: {e}")
        
        # Set defaults for known emotes that don't have configs
        for emote in self.known_emotes:
            if emote not in configs:
                configs[emote] = EmoteConfig(is_emote=True)
        
        return configs
    
    def save_emote_configs(self) -> None:
        """Save emote and word configurations."""
        config_path = os.path.join(self.base_dir, 'emote_configs.json')
        
        data = {}
        for key, cfg in self.emote_configs.items():
            data[key] = {
                'is_emote': cfg.is_emote,
                'custom_audio': cfg.custom_audio,
                'color': cfg.color,
                'font': cfg.font,
                'size': cfg.size,
                'display_time': cfg.display_time,
                'combo_timeout': cfg.combo_timeout,
                'show_in_overlay': cfg.show_in_overlay,
                'animation': cfg.animation
            }
        
        write_json_file(config_path, data)
        logger.info("Emote configurations saved")
    
    def _init_components(self) -> None:
        """Initialize all component managers."""
        # Initialize audio manager
        self.audio_manager = AudioManager()
        self.audio_manager.configure_tts(
            enabled=self.config.getboolean('TTS', 'enabled', fallback=True),
            rate=int(self.config.get('TTS', 'rate', fallback='150')),
            volume=float(self.config.get('TTS', 'volume', fallback='0.8'))
        )
        
        # Initialize OBS manager
        self.obs_manager = OBSManager(
            host=self.config.get('OBS', 'host', fallback='localhost'),
            port=int(self.config.get('OBS', 'port', fallback='4444')),
            password=self.config.get('OBS', 'password', fallback='')
        )
        
        # Initialize combo manager
        self.combo_manager = ComboManager(
            default_combo_timeout=self.default_combo_timeout,
            default_display_time=self.default_display_time,
            allow_multiple_from_user=self.allow_multiple_from_user
        )
        
        # Initialize overlay manager
        static_dir = os.path.join(self.base_dir, 'static')
        ensure_directory(static_dir)  # Create static directory if it doesn't exist
        overlay_path = os.path.join(static_dir, 'overlay_data.json')
        self.overlay_manager = OverlayManager(overlay_path)
        
        # Initialize emote providers
        self.twitch_emotes = TwitchEmoteProvider()
        self.bttv_emotes = BTTVEmoteProvider()
        self.ffz_emotes = FFZEmoteProvider()
        self.seventv_emotes = SevenTVEmoteProvider()
        
        # Combined emote dictionary
        self.all_emotes = {}
        
        # Create a thread-safe event loop for async operations
        self.loop = asyncio.new_event_loop()
        
        # Message queue for synchronized processing
        self.message_queue = Queue()
        
        # Run the async event loop in a daemon thread
        def run_async_loop():
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        self.loop_thread = threading.Thread(target=run_async_loop, daemon=True)
        self.loop_thread.start()
    
    def connect_to_twitch(self) -> bool:
        """
        Connect to Twitch IRC.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.sock = socket.socket()
            self.sock.connect((self.server, self.port))
            self.sock.send(f"PASS {self.token}\n".encode('utf-8'))
            self.sock.send(f"NICK {self.nickname}\n".encode('utf-8'))
            self.sock.send(f"JOIN #{self.channel}\n".encode('utf-8'))
            
            # Request tags capability for emote data
            self.sock.send("CAP REQ :twitch.tv/tags\n".encode('utf-8'))
            
            logger.info(f"Connected to Twitch channel #{self.channel}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Twitch: {e}")
            self.sock = None
            return False
    
    async def fetch_all_emotes(self) -> Dict[str, Any]:
        """
        Fetch emotes from all providers.
        
        Returns:
            Dict[str, Any]: Combined dictionary of all emotes
        """
        try:
            # Run all fetch operations concurrently
            tasks = [
                self.bttv_emotes.fetch_emotes(self.channel_id),
                self.ffz_emotes.fetch_emotes(self.channel),
                self.seventv_emotes.fetch_emotes(self.channel_id)
            ]
            
            # Wait for all tasks to complete
            results = [await task for task in tasks]
            
            # Combine results into all_emotes dictionary
            combined = {}
            for emotes in results:
                combined.update(emotes)
                
            # Add to known emotes
            self.known_emotes.update(combined.keys())
            self.save_known_emotes()
            
            # Update instance variable
            self.all_emotes = combined
            
            logger.info(f"Loaded {len(combined)} emotes from all providers")
            return combined
        except Exception as e:
            logger.error(f"Error fetching emotes: {e}")
            return {}
    
    def get_emote_url(self, emote_name: str, emote_id: Optional[str] = None, provider_type: Optional[str] = None) -> Optional[str]:
        """
        Get emote URL from the appropriate provider.
        
        Args:
            emote_name: Name of the emote
            emote_id: Optional ID of the emote
            provider_type: Optional provider type ('twitch', 'bttv', 'ffz', '7tv')
            
        Returns:
            Optional[str]: URL of the emote or None if not found
        """
        try:
            # Check if we have this emote in all_emotes
            if emote_name in self.all_emotes:
                emote_data = self.all_emotes[emote_name]
                provider_type = emote_data.get('type')
                emote_id = emote_data.get('id')
                
                # If URL is directly stored (FFZ)
                if 'url' in emote_data:
                    return emote_data['url']
            
            # Return URL based on provider type
            if provider_type == 'twitch' and emote_id:
                return self.twitch_emotes.get_emote_url(emote_id)
            elif provider_type == 'bttv' and emote_id:
                return self.bttv_emotes.get_emote_url(emote_id)
            elif provider_type == 'ffz' and emote_id:
                return self.ffz_emotes.get_emote_url(emote_id)
            elif provider_type == '7tv' and emote_id:
                return self.seventv_emotes.get_emote_url(emote_id)
                
            # Fallback for Twitch emotes
            if emote_id:
                return self.twitch_emotes.get_emote_url(emote_id)
                
            return None
        except Exception as e:
            logger.error(f"Error getting emote URL: {e}")
            return None
    
    async def download_emote(self, emote_id: str, emote_url: str, emote_type: str = "twitch", emote_name: str = "") -> Optional[str]:
        """
        Download an emote image and save it locally.
        
        Args:
            emote_id: ID of the emote
            emote_url: URL of the emote
            emote_type: Type of the emote provider
            emote_name: Name of the emote (for filename)
            
        Returns:
            Optional[str]: Path to the downloaded emote or None if failed
        """
        try:
            import requests
            import shutil
            
            # Make sure emote_name is provided for Twitch emotes
            if emote_type == "twitch" and not emote_name and emote_id:
                emote_name = f"twitch_emote_{emote_id}"
                
            # Create a filename based on type, ID and name
            if emote_name:
                # Create a safe filename from emote name
                safe_name = "".join(c for c in emote_name if c.isalnum() or c in "._- ")
                filename = f"{emote_type}_{safe_name}_{emote_id}.png"
            else:
                filename = f"{emote_type}_{emote_id}.png"
                
            file_path = os.path.join(self.emotes_dir, filename)
            
            # Ensure emotes directory exists
            ensure_directory(self.emotes_dir)
            
            # Skip if already downloaded
            if os.path.exists(file_path):
                logger.debug(f"Emote already exists: {file_path}")
                
                # Copy to static directory if needed
                static_dir = os.path.join(self.base_dir, 'static')
                static_emotes_dir = os.path.join(static_dir, 'emotes')
                
                # Ensure static directories exist
                ensure_directory(static_dir)
                ensure_directory(static_emotes_dir)
                
                static_file_path = os.path.join(static_emotes_dir, filename)
                
                # Copy if not already in static directory
                if not os.path.exists(static_file_path):
                    shutil.copy2(file_path, static_file_path)
                    logger.debug(f"Copied existing emote to static: {static_file_path}")
                
                return file_path
                
            # For Twitch emotes, construct the URL directly if not provided
            if emote_type == "twitch" and emote_id and not emote_url:
                emote_url = f"https://static-cdn.jtvnw.net/emoticons/v2/{emote_id}/default/dark/3.0"
            
            # Download the emote
            logger.info(f"Downloading emote {emote_name or emote_id} from {emote_url}")
            response = requests.get(emote_url, timeout=5)
            response.raise_for_status()
            
            # Save the emote
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded emote: {emote_name or emote_id} ({emote_type}) to {file_path}")
            
            # Copy to static directory for overlay
            static_dir = os.path.join(self.base_dir, 'static')
            static_emotes_dir = os.path.join(static_dir, 'emotes')
            
            # Ensure static directories exist
            ensure_directory(static_dir)
            ensure_directory(static_emotes_dir)
            
            static_file_path = os.path.join(static_emotes_dir, filename)
            shutil.copy2(file_path, static_file_path)
            logger.debug(f"Copied emote to static: {static_file_path}")
            
            return file_path
        except Exception as e:
            logger.error(f"Failed to download emote {emote_name or emote_id} ({emote_type}): {e}")
            return None
    
    def _download_emote(self, emote_id: str, emote_url: str, emote_type: str = "twitch", emote_name: str = "") -> Optional[str]:
        """
        Download an emote image synchronously.
        
        Args:
            emote_id: ID of the emote
            emote_url: URL of the emote
            emote_type: Type of the emote provider
            emote_name: Name of the emote
            
        Returns:
            Optional[str]: Path to the downloaded emote or None if failed
        """
        try:
            download_future = asyncio.run_coroutine_threadsafe(
                self.download_emote(emote_id, emote_url, emote_type, emote_name),
                self.loop
            )
            
            # Wait for the download to complete
            local_path = download_future.result(5.0)  # Increased timeout
            return local_path
        except Exception as e:
            logger.error(f"Error downloading emote {emote_name} ({emote_id}): {e}")
            return None
    
    def _get_emote_path(self, emote_id: str, emote_type: str = "twitch", emote_name: str = "") -> Optional[str]:
        """
        Get the local path for an emote, creating filename from emote details.
        
        Args:
            emote_id: ID of the emote
            emote_type: Type of the emote provider
            emote_name: Name of the emote
            
        Returns:
            Optional[str]: Path to the emote or None
        """
        if not emote_id:
            return None
            
        # Create a filename based on type, ID and name
        if emote_name:
            # Create a safe filename from emote name
            safe_name = "".join(c for c in emote_name if c.isalnum() or c in "._- ")
            filename = f"{emote_type}_{safe_name}_{emote_id}.png"
        else:
            filename = f"{emote_type}_{emote_id}.png"
        
        # For the overlay, we need a relative path
        return f"emotes/{filename}"
    
    def process_message(self, username: str, message: str, emote_data: Optional[str] = None) -> None:
        """
        Process a chat message to count words and emotes.
        
        Args:
            username: Username of the sender
            message: Message content
            emote_data: Optional emote data from Twitch tags
        """
        # Extract emote information from the Twitch emote data
        emote_info = {}
        if emote_data and emote_data != '':
            try:
                # Twitch format: emote_id:start-end,start-end/emote_id:start-end
                for emote_part in emote_data.split('/'):
                    if not emote_part:
                        continue
                    parts = emote_part.split(':')
                    if len(parts) != 2:
                        continue
                        
                    emote_id = parts[0]
                    positions = parts[1].split(',')
                    
                    for pos in positions:
                        if not pos:
                            continue
                        start_end = pos.split('-')
                        if len(start_end) != 2:
                            continue
                        
                        try:
                            start, end = int(start_end[0]), int(start_end[1])
                            if start < len(message) and end < len(message):
                                # Extract the emote text from the message
                                emote_text = message[start:end+1]
                                # Store the mapping of emote text to ID
                                emote_info[emote_text] = emote_id
                                
                                # Add to known emotes
                                if emote_text not in self.known_emotes:
                                    self.known_emotes.add(emote_text)
                                    if emote_text not in self.emote_configs:
                                        self.emote_configs[emote_text] = EmoteConfig(is_emote=True)
                        except (ValueError, IndexError) as e:
                            logger.error(f"Error parsing emote position {pos}: {e}")
            except Exception as e:
                logger.error(f"Error parsing emote data {emote_data}: {e}")
        
        # Extract individual words
        words = message.strip().split()
        
        # Check if the message is short enough to process as a whole
        if len(words) <= self.max_words_per_message:
            # Process the whole message based on the content
            # If it contains emotes, process them individually
            if emote_info:
                for emote_text, emote_id in emote_info.items():
                    # Create emote URL
                    emote_url = f"https://static-cdn.jtvnw.net/emoticons/v2/{emote_id}/default/dark/3.0"
                    
                    # Download the emote
                    local_path = self._download_emote(emote_id, emote_url, "twitch", emote_text)
                    relative_path = None
                    if local_path:
                        # Get relative path for the overlay
                        filename = os.path.basename(local_path)
                        relative_path = f"emotes/{filename}"
                    
                    self._process_emote(emote_text, username, emote_id, emote_url, relative_path)
            else:
                # No emotes, process as a phrase
                self._process_phrase(message.strip(), username, emote_data, message)
        else:
            # For longer messages, only process emotes
            if emote_info:
                for emote_text, emote_id in emote_info.items():
                    # Create emote URL
                    emote_url = f"https://static-cdn.jtvnw.net/emoticons/v2/{emote_id}/default/dark/3.0"
                    
                    # Download the emote
                    local_path = self._download_emote(emote_id, emote_url, "twitch", emote_text)
                    relative_path = None
                    if local_path:
                        # Get relative path for the overlay
                        filename = os.path.basename(local_path)
                        relative_path = f"emotes/{filename}"
                    
                    self._process_emote(emote_text, username, emote_id, emote_url, relative_path)
            else:
                # Check if any known emotes are in the message
                for word in words:
                    if word in self.known_emotes:
                        # Try to process this known emote
                        self._process_word(word, username, emote_data, message)
    
    def _process_emote(self, emote_text: str, username: str, emote_id: str, emote_url: str, local_emote_path: Optional[str] = None) -> None:
        """
        Process a single emote.
        
        Args:
            emote_text: The emote text
            username: The username of the sender
            emote_id: The emote ID
            emote_url: The emote URL
            local_emote_path: Optional path to local emote image
        """
        # First check if we have a config for this emote
        config = self.emote_configs.get(emote_text)
        if not config:
            # Create default config
            self.emote_configs[emote_text] = EmoteConfig(is_emote=True)
            config = self.emote_configs[emote_text]
        
        # Add or update combo
        combo_count, is_new = self.combo_manager.add_or_update_combo(
            emote_text, 
            username, 
            is_emote=True, 
            emote_id=emote_id, 
            emote_url=emote_url,
            config=config,
            local_emote_path=local_emote_path
        )
        
        # Add to message queue for processing
        self.message_queue.put({
            "word": emote_text,
            "combo": combo_count,
            "is_emote": True,
            "emote_id": emote_id,
            "emote_url": emote_url,
            "local_emote_path": local_emote_path,
            "custom_audio": config.custom_audio if config else None,
            "username": username
        })
        
        # Update overlay
        self.update_overlay()
        
        # Save emotes and configs periodically
        if len(self.known_emotes) % 10 == 0:
            self.save_known_emotes()
            self.save_emote_configs()
    
    def _process_word(self, word: str, username: str, emote_data: Optional[str] = None, full_message: str = "") -> None:
        """
        Process a single word or emote.
        
        Args:
            word: The word to process
            username: The username of the sender
            emote_data: Optional emote data from Twitch tags
            full_message: Original full message for context
        """
        # Skip common articles, prepositions, etc. and words that are too short based on settings
        # Always process known emotes regardless of length
        if word not in self.known_emotes and (len(word) < self.min_word_length or 
                                              word.lower() in {'the', 'and', 'or', 'but', 'for', 'not', 'with'}):
            return
        
        # Extract emote IDs if available
        emote_map = {}
        if emote_data and emote_data != '':
            try:
                emote_parts = emote_data.split('/')
                for part in emote_parts:
                    if not part:
                        continue
                    id_ranges = part.split(':')
                    if len(id_ranges) < 2:
                        continue
                    emote_id = id_ranges[0]
                    positions = id_ranges[1].split(',')
                    for pos in positions:
                        if not pos:
                            continue
                        start_end = pos.split('-')
                        if len(start_end) != 2:
                            continue
                        try:
                            start, end = int(start_end[0]), int(start_end[1])
                            if start < len(full_message) and end < len(full_message):
                                extracted_word = full_message[start:end+1]
                                emote_map[extracted_word] = {"id": emote_id, "type": "twitch"}
                        except (ValueError, IndexError) as e:
                            logger.error(f"Error parsing emote position {pos}: {e}")
            except Exception as e:
                logger.error(f"Error parsing emote data {emote_data}: {e}")
        
        # Determine if this is an emote and get its details
        is_emote = False
        emote_id = None
        emote_url = None
        emote_type = None
        local_path = None
        # Check if it's a Twitch emote from emote_map
        if word in emote_map:
            is_emote = True
            emote_id = emote_map[word]["id"]
            emote_type = "twitch"
            emote_url = f"https://static-cdn.jtvnw.net/emoticons/v2/{emote_id}/default/dark/3.0"
            
            # Try to download the emote immediately
            try:
                local_path = self._download_emote(emote_id, emote_url, emote_type, word)
                if local_path:
                    logger.info(f"Downloaded Twitch emote {word} to {local_path}")
                    # Prepare the path for the overlay
                    filename = os.path.basename(local_path)
                    local_emote_path = f"emotes/{filename}"
                else:
                    local_emote_path = None
            except Exception as e:
                logger.error(f"Error downloading Twitch emote {word}: {e}")
                local_emote_path = None
            
            # Ensure it's in known emotes
            if word not in self.known_emotes:
                self.known_emotes.add(word)
                if word not in self.emote_configs:
                    self.emote_configs[word] = EmoteConfig(is_emote=True)
        # Check if it's in our known emotes dictionary
        elif word in self.all_emotes:
            is_emote = True
            emote_data = self.all_emotes[word]
            emote_id = emote_data.get('id')
            emote_type = emote_data.get('type')
            if 'url' in emote_data:
                emote_url = emote_data['url']
        # Check if it's in our known emotes set
        elif word in self.known_emotes:
            is_emote = True
            # Try to generate ID for Twitch emotes
            # First check if the emote is a common Twitch emote
            common_emotes = {
                "Kappa": "25", 
                "PogChamp": "88", 
                "LUL": "425618", 
                "BibleThump": "86", 
                "TriHard": "120232", 
                "Kreygasm": "41", 
                "4Head": "354", 
                "SwiftRage": "34", 
                "NotLikeThis": "58765", 
                "ResidentSleeper": "245", 
                "DansGame": "33", 
                "FrankerZ": "65", 
                "SMOrc": "52", 
                "KappaPride": "55338", 
                "CoolStoryBob": "123171", 
                "cmonBruh": "84608", 
                "VoHiYo": "81274", 
                "TTours": "38436"
            }
            
            if word in common_emotes:
                emote_id = common_emotes[word]
                emote_type = "twitch"
                emote_url = f"https://static-cdn.jtvnw.net/emoticons/v2/{emote_id}/default/dark/3.0"
                
                # Try to download the emote immediately
                try:
                    local_path = self._download_emote(emote_id, emote_url, emote_type, word)
                    if local_path:
                        logger.info(f"Downloaded common Twitch emote {word} to {local_path}")
                        # Prepare the path for the overlay
                        filename = os.path.basename(local_path)
                        local_emote_path = f"emotes/{filename}"
                    else:
                        local_emote_path = None
                except Exception as e:
                    logger.error(f"Error downloading common Twitch emote {word}: {e}")
                    local_emote_path = None
        
        # Add or update combo
        config = self.emote_configs.get(word)
        if not config:
            self.emote_configs[word] = EmoteConfig(is_emote=is_emote)
            config = self.emote_configs[word]
        
        # Prepare local emote path
        local_emote_path = None
        if local_path:
            filename = os.path.basename(local_path)
            local_emote_path = f"emotes/{filename}"
        
        combo_count, is_new = self.combo_manager.add_or_update_combo(
            word, 
            username, 
            is_emote=is_emote, 
            emote_id=emote_id, 
            emote_url=emote_url,
            config=config,
            local_emote_path=local_emote_path
        )
        
        # Add to message queue for processing
        self.message_queue.put({
            "word": word,
            "combo": combo_count,
            "is_emote": is_emote,
            "emote_id": emote_id,
            "emote_url": emote_url,
            "local_emote_path": local_emote_path,
            "custom_audio": config.custom_audio if config else None,
            "username": username
        })
        
        # Update overlay with active combos
        self.update_overlay()
        
        # Save emotes and configs periodically
        if len(self.known_emotes) % 10 == 0:
            self.save_known_emotes()
            self.save_emote_configs()
    
    def _process_phrase(self, phrase: str, username: str, emote_data: Optional[str] = None, full_message: str = "") -> None:
        """
        Process a complete phrase (which may be multiple words).
        
        Args:
            phrase: The phrase to process
            username: The username of the sender
            emote_data: Optional emote data from Twitch tags
            full_message: Original full message for context
        """
        # Skip common phrases and phrases that are too short based on settings
        if len(phrase) < self.min_word_length:
            return
        
        # Check if this phrase contains any known emotes
        contains_emote = False
        for emote in self.known_emotes:
            if emote in phrase.split():
                contains_emote = True
                break
        
        # Add or update combo
        config = self.emote_configs.get(phrase)
        if not config:
            # Create a default config for this phrase if it doesn't exist
            is_emote = contains_emote
            self.emote_configs[phrase] = EmoteConfig(is_emote=is_emote)
            config = self.emote_configs[phrase]
        
        # Use local emote path and emote URLs for phrases containing emotes
        local_path = None
        emote_url = None
        emote_id = None
        emote_type = None
        
        combo_count, is_new = self.combo_manager.add_or_update_combo(
            phrase, 
            username, 
            is_emote=config.is_emote, 
            emote_id=emote_id, 
            emote_url=emote_url,
            config=config,
            local_emote_path=local_path
        )
        
        # Add to message queue for processing
        self.message_queue.put({
            "word": phrase,
            "combo": combo_count,
            "is_emote": config.is_emote,
            "emote_id": emote_id,
            "emote_url": emote_url,
            "local_emote_path": local_path,
            "custom_audio": config.custom_audio if config else None,
            "username": username
        })
        
        # Update overlay with active combos
        self.update_overlay()
        
        # Save configs periodically
        if len(self.emote_configs) % 10 == 0:
            self.save_emote_configs()
    
    def update_overlay(self) -> None:
        """Update the overlay with active combos."""
        combo_items = self.combo_manager.get_active_combos()
        
        # Make sure static directory exists
        static_dir = os.path.join(self.base_dir, 'static')
        if not os.path.exists(static_dir):
            os.makedirs(static_dir, exist_ok=True)
        
        self.overlay_manager.update_overlay_with_combos(combo_items)
    
    def process_message_queue(self) -> None:
        """Process the message queue to synchronize TTS and display."""
        while self.running:
            try:
                # Get item from queue with timeout
                message = self.message_queue.get(timeout=0.1)
                
                # Update overlay first
                self.update_overlay()
                
                # Play audio or TTS
                if message.get("custom_audio"):
                    self.audio_manager.play_audio_file(message["custom_audio"])
                elif not message.get("is_emote", False) and self.audio_manager.tts_enabled:
                    # Speak the word with its combo count if applicable
                    text = f"{message['word']}"
                    if message["combo"] > 1:
                        text += f" {message['combo']}"
                    
                    # Log for debugging
                    logger.info(f"Speaking text: '{text}', TTS enabled: {self.audio_manager.tts_enabled}")
                    result = self.audio_manager.speak_text(text)
                    logger.info(f"TTS result: {result}")
                
                # Mark task as done
                self.message_queue.task_done()
            except Empty:  # Using the proper Empty exception from queue module
                # No messages, just wait
                pass
            except Exception as e:
                logger.error(f"Error processing message queue: {e}")
    
    def listen_to_chat(self) -> None:
        """Listen to Twitch chat and process messages."""
        if not self.connect_to_twitch():
            logger.error("Failed to connect to Twitch chat")
            return
        
        buffer = ""
        self.sock.settimeout(0.1)  # Set a short timeout for more responsive reading
        
        while self.running:
            try:
                data = self.sock.recv(2048)
                if not data:
                    logger.warning("No data received from Twitch, reconnecting...")
                    if not self.connect_to_twitch():
                        time.sleep(5)  # Wait before retry
                    continue
                
                buffer += data.decode('utf-8')
                lines = buffer.split("\r\n")
                buffer = lines.pop()
                
                for line in lines:
                    if line.startswith('PING'):
                        self.sock.send("PONG :tmi.twitch.tv\r\n".encode('utf-8'))
                    elif 'PRIVMSG' in line:
                        # Parse username and message
                        username_pattern = r":(.*?)!"
                        message_pattern = r"PRIVMSG #[^:]*:(.*)"
                        
                        username_match = re.search(username_pattern, line)
                        message_match = re.search(message_pattern, line)
                        
                        if username_match and message_match:
                            username = username_match.group(1)
                            message = message_match.group(1)
                            
                            # Extract emote data if available
                            emote_data = None
                            if '@badges=' in line:  # This indicates tags are present
                                emote_tags = re.search(r"emotes=(.*?)[; ]", line)
                                if emote_tags:
                                    emote_data = emote_tags.group(1)
                            
                            # Process the message
                            self.process_message(username, message, emote_data)
            except socket.timeout:
                # This is expected due to our timeout setting - just continue
                continue
            except Exception as e:
                logger.error(f"Error in chat listener: {e}")
                # Try to reconnect
                try:
                    if not self.connect_to_twitch():
                        time.sleep(5)  # Wait before retry
                except:
                    time.sleep(5)  # Wait before retry
    
    def start(self) -> bool:
        """
        Start the Twitch tracker.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.running:
            logger.warning("Tracker is already running")
            return False
            
        self.running = True
        
        # Start the combo manager
        self.combo_manager.start()
        
        # Connect to OBS
        self.obs_manager.connect()
        
        # Fetch emotes
        asyncio.run_coroutine_threadsafe(self.fetch_all_emotes(), self.loop)
        
        # Start chat listener thread
        self.chat_thread = threading.Thread(target=self.listen_to_chat)
        self.chat_thread.daemon = True
        self.chat_thread.start()
        
        # Start message processing thread
        self.processing_thread = threading.Thread(target=self.process_message_queue)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        logger.info("Twitch Tracker started")
        return True
    
    def stop(self) -> None:
        """Stop the Twitch tracker."""
        if not self.running:
            return
            
        self.running = False
        
        # Stop the combo manager
        self.combo_manager.stop()
        
        # Close socket
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        
        # Disconnect from OBS
        self.obs_manager.disconnect()
        
        # Stop async event loop
        try:
            self.loop.call_soon_threadsafe(self.loop.stop)
        except:
            pass
            
        logger.info("Twitch Tracker stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get current tracking statistics.
        
        Returns:
            Dict[str, Any]: Dictionary of statistics
        """
        word_counts = dict(self.combo_manager.word_counts)
        active_combos = self.combo_manager.get_active_combos()
        
        # Calculate additional stats
        total_emotes = sum(count for word, count in word_counts.items() 
                         if word in self.known_emotes)
        
        # Find top emote
        top_emote = None
        top_count = 0
        for word, count in word_counts.items():
            if word in self.known_emotes and count > top_count:
                top_emote = word
                top_count = count
        
        # Find largest combo
        largest_combo = 0
        for combo in active_combos:
            if combo["combo"] > largest_combo:
                largest_combo = combo["combo"]
        
        return {
            "word_counts": word_counts,
            "active_combos": active_combos,
            "total_emotes": total_emotes,
            "top_emote": top_emote,
            "top_emote_count": top_count if top_emote else 0,
            "largest_combo": largest_combo
        }
    
    def clear_stats(self) -> None:
        """Clear all tracking statistics."""
        self.combo_manager.clear_all_stats()
        self.update_overlay()
        logger.info("All tracking statistics cleared")