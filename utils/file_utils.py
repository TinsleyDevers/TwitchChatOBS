"""
File utility functions for the Twitch Tracker application.
"""
import os
import json
import logging
from typing import Dict, Set, Any

logger = logging.getLogger("TwitchTracker.FileUtils")


def ensure_directory(directory_path: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory
    """
    os.makedirs(directory_path, exist_ok=True)


def write_json_file(file_path: str, data: Dict[str, Any]) -> bool:
    """
    Write data to a JSON file atomically.
    
    Args:
        file_path: Path to the JSON file
        data: Data to write
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure the directory exists
        directory = os.path.dirname(file_path)
        ensure_directory(directory)
        
        # Write data to a temporary file first, then rename for atomic update
        temp_file = f"{file_path}.tmp"
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # On Windows, we need to remove the destination file first
        if os.path.exists(file_path) and os.name == 'nt':
            os.remove(file_path)
            
        # Rename temp file to final destination
        os.rename(temp_file, file_path)
        return True
        
    except Exception as e:
        logger.error(f"Failed to write JSON file {file_path}: {e}")
        return False


def read_json_file(file_path: str, default: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Read data from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        default: Default value if the file doesn't exist or is invalid
        
    Returns:
        Dict[str, Any]: Data from the JSON file or the default value
    """
    if default is None:
        default = {}
        
    try:
        if not os.path.exists(file_path):
            return default
            
        with open(file_path, 'r') as f:
            return json.load(f)
            
    except Exception as e:
        logger.error(f"Failed to read JSON file {file_path}: {e}")
        return default


def load_text_file_as_set(file_path: str, comment_char: str = '#') -> Set[str]:
    """
    Load a text file into a set, skipping empty lines and comments.
    
    Args:
        file_path: Path to the text file
        comment_char: Character that indicates a comment line
        
    Returns:
        Set[str]: Set of non-empty, non-comment lines
    """
    result = set()
    
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith(comment_char):
                        result.add(line)
    except Exception as e:
        logger.error(f"Failed to load text file {file_path}: {e}")
        
    return result


def save_set_to_text_file(file_path: str, data: Set[str], header: str = None) -> bool:
    """
    Save a set to a text file, one item per line.
    
    Args:
        file_path: Path to the text file
        data: Set of strings to save
        header: Optional header comment to add at the top of the file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(file_path, 'w') as f:
            if header:
                f.write(f"{header}\n")
                
            for item in sorted(data):
                f.write(f"{item}\n")
                
        return True
        
    except Exception as e:
        logger.error(f"Failed to save text file {file_path}: {e}")
        return False