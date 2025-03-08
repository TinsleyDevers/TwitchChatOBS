"""
Overlay management for the Twitch Tracker application.
"""
import os
import logging
from typing import Dict, List, Any, Optional
from utils.file_utils import write_json_file

logger = logging.getLogger("TwitchTracker.OverlayManager")


class OverlayManager:
    """
    Manager for overlay files and web content.
    Handles creating and updating the overlay JSON data.
    """
    
    def __init__(self, overlay_path: str, html_template_path: Optional[str] = None):
        """
        Initialize the OverlayManager.
        
        Args:
            overlay_path: Path to the overlay JSON data file
            html_template_path: Optional path to the HTML template file
        """
        self.overlay_path = overlay_path
        self.html_template_path = html_template_path
        self.create_empty_overlay()
    
    def create_empty_overlay(self) -> bool:
        """
        Create an empty overlay data file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self.update_overlay({"items": []})
    
    def update_overlay(self, data: Dict[str, Any]) -> bool:
        """
        Update the overlay data file.
        
        Args:
            data: Overlay data to write
            
        Returns:
            bool: True if successful, False otherwise
        """
        result = write_json_file(self.overlay_path, data)
        if result:
            logger.debug(f"Updated overlay file with {len(data.get('items', []))} items")
        return result
    
    def update_overlay_with_combos(self, combo_items: List[Dict[str, Any]], max_items: int = 5) -> bool:
        """
        Update the overlay with combo items.
        
        Args:
            combo_items: List of combo items to display
            max_items: Maximum number of items to include
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Sort by combo count (highest first)
        sorted_items = sorted(combo_items, key=lambda x: x.get("combo", 0), reverse=True)
        
        # Limit to max_items
        if len(sorted_items) > max_items:
            sorted_items = sorted_items[:max_items]
        
        return self.update_overlay({"items": sorted_items})
    
    def create_html_overlay(self) -> bool:
        """
        Create or update the HTML overlay file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.html_template_path:
            logger.warning("No HTML template path provided")
            return False
            
        try:
            with open(self.html_template_path, 'r') as f:
                html_content = f.read()
                
            # Write the HTML file to the same directory as the overlay JSON
            html_path = os.path.join(os.path.dirname(self.overlay_path), 'overlay.html')
            
            with open(html_path, 'w') as f:
                f.write(html_content)
                
            logger.info(f"Created HTML overlay at {html_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create HTML overlay: {e}")
            return False