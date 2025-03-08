"""
Combo management for the Twitch Tracker application.
"""
import time
import logging
import threading
from typing import Dict, List, Set, Optional, Tuple, Any
from collections import Counter
from core.data_models import ComboItem, EmoteConfig

logger = logging.getLogger("TwitchTracker.ComboManager")


class ComboManager:
    """
    Manager for tracking emote/word combos and their statistics.
    """
    
    def __init__(self, 
                 default_combo_timeout: int = 10,
                 default_display_time: int = 5,
                 allow_multiple_from_user: bool = True):
        """
        Initialize the ComboManager.
        
        Args:
            default_combo_timeout: Default timeout for combos in seconds
            default_display_time: Default display time for items in seconds
            allow_multiple_from_user: Whether to allow multiple contributions from the same user
        """
        self.default_combo_timeout = default_combo_timeout
        self.default_display_time = default_display_time
        self.allow_multiple_from_user = allow_multiple_from_user
        
        # Tracking data
        self.word_counts = Counter()
        self.current_combos = {}  # Dict[str, ComboItem]
        
        # Thread management
        self.running = False
        self.cleanup_thread = None
        self.lock = threading.Lock()
    
    def start(self) -> None:
        """Start the combo manager and cleanup thread."""
        with self.lock:
            if not self.running:
                self.running = True
                self.cleanup_thread = threading.Thread(target=self._cleanup_expired_combos)
                self.cleanup_thread.daemon = True
                self.cleanup_thread.start()
                logger.info("ComboManager started")
    
    def stop(self) -> None:
        """Stop the combo manager and cleanup thread."""
        with self.lock:
            if self.running:
                self.running = False
                # Cleanup thread will exit on next iteration
                logger.info("ComboManager stopped")
    
    def add_or_update_combo(self, 
                           word: str, 
                           username: str, 
                           is_emote: bool = False,
                           emote_id: Optional[str] = None,
                           emote_url: Optional[str] = None,
                           config: Optional[EmoteConfig] = None) -> Tuple[int, bool]:
        """
        Add or update a combo for a word/emote.
        
        Args:
            word: The word or emote text
            username: The username of the contributor
            is_emote: Whether this is an emote (True) or word (False)
            emote_id: Optional emote ID
            emote_url: Optional emote URL
            config: Optional config for this word/emote
            
        Returns:
            Tuple[int, bool]: (combo count, is new combo)
        """
        with self.lock:
            # Increment the total count
            self.word_counts[word] += 1
            
            # Get timeout from config or use default
            timeout = self.default_combo_timeout
            if config:
                timeout = config.combo_timeout
            
            # Check if combo already exists and is not expired
            now = time.time()
            is_new_combo = True
            
            if word in self.current_combos and now < self.current_combos[word].expires:
                combo_item = self.current_combos[word]
                
                # Check if user already contributed and respect toggle setting
                if not self.allow_multiple_from_user and username in combo_item.contributors:
                    logger.debug(f"Skipping {word} from {username} (already contributed)")
                    return combo_item.combo, False
                
                # Update existing combo
                combo_item.combo += 1
                combo_item.contributors.add(username)
                combo_item.expires = now + timeout
                is_new_combo = False
            else:
                # Create new combo
                self.current_combos[word] = ComboItem(
                    text=word,
                    combo=1,
                    is_emote=is_emote,
                    emote_id=emote_id,
                    emote_url=emote_url,
                    expires=now + timeout,
                    contributors={username}
                )
            
            return self.current_combos[word].combo, is_new_combo
    
    def get_active_combos(self) -> List[Dict[str, Any]]:
        """
        Get all active combos as a list of dictionaries.
        
        Returns:
            List[Dict[str, Any]]: List of combo data dictionaries
        """
        with self.lock:
            result = []
            for word, combo_item in self.current_combos.items():
                result.append({
                    "text": combo_item.text,
                    "combo": combo_item.combo,
                    "is_emote": combo_item.is_emote,
                    "emote_id": combo_item.emote_id,
                    "emote_url": combo_item.emote_url,
                    "expires": int(combo_item.expires * 1000),  # Convert to milliseconds for JS
                    "contributors": list(combo_item.contributors)
                })
            return result
    
    def get_top_combo(self) -> Optional[Dict[str, Any]]:
        """
        Get the top active combo.
        
        Returns:
            Optional[Dict[str, Any]]: Top combo data or None if no active combos
        """
        combos = self.get_active_combos()
        if not combos:
            return None
            
        return max(combos, key=lambda x: x["combo"])
    
    def get_combo(self, word: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific combo.
        
        Args:
            word: The word or emote to get
            
        Returns:
            Optional[Dict[str, Any]]: Combo data or None if not found
        """
        with self.lock:
            if word not in self.current_combos:
                return None
                
            combo_item = self.current_combos[word]
            return {
                "text": combo_item.text,
                "combo": combo_item.combo,
                "is_emote": combo_item.is_emote,
                "emote_id": combo_item.emote_id,
                "emote_url": combo_item.emote_url,
                "expires": int(combo_item.expires * 1000),  # Convert to milliseconds for JS
                "contributors": list(combo_item.contributors)
            }
    
    def clear_combo(self, word: str) -> bool:
        """
        Clear a specific combo.
        
        Args:
            word: The word or emote to clear
            
        Returns:
            bool: True if the combo was cleared, False if not found
        """
        with self.lock:
            if word in self.current_combos:
                del self.current_combos[word]
                return True
            return False
    
    def clear_all_combos(self) -> None:
        """Clear all active combos."""
        with self.lock:
            self.current_combos.clear()
    
    def clear_all_stats(self) -> None:
        """Clear all combo statistics."""
        with self.lock:
            self.word_counts.clear()
            self.current_combos.clear()
    
    def _cleanup_expired_combos(self) -> None:
        """Background thread to clean up expired combos."""
        while self.running:
            time.sleep(1)  # Check every second
            
            with self.lock:
                now = time.time()
                expired_combos = [word for word, combo_item in self.current_combos.items() 
                              if now > combo_item.expires]
                
                if expired_combos:
                    for word in expired_combos:
                        del self.current_combos[word]
                    
                    logger.debug(f"Cleaned up {len(expired_combos)} expired combos")