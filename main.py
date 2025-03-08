"""
Main entry point for the Twitch Tracker application.
"""
import os
import sys
import logging
from utils.logging_setup import setup_logging
from core.tracker import TwitchTracker
from ui.main_window import TwitchTrackerGUI
from utils.html_generator import create_html_overlay


def main():
    """Main entry point for the application."""
    try:
        # Set up logging
        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "twitch_tracker.log")
        logger = setup_logging(log_file)
        
        logger.info("Starting TwitchTracker")
        
        # Initialize tracker
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
        tracker = TwitchTracker(config_path)
        logger.info("TwitchTracker initialized")
        
        # Create static directory if it doesn't exist
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
        os.makedirs(static_dir, exist_ok=True)
        
        # Create HTML overlay
        html_path = os.path.join(static_dir, "overlay.html")
        if create_html_overlay(html_path):
            logger.info(f"HTML overlay created at: {html_path}")
            print(f"HTML overlay created at: {html_path}")
            print("Add this as a Browser Source in OBS with 'Local file' checked")
        
        # Start GUI
        logger.info("Initializing GUI")
        gui = TwitchTrackerGUI(tracker)
        print("Starting GUI main loop")
        gui.run()
        logger.info("GUI closed")
    
    except Exception as e:
        print(f"Error in main: {e}")
        logger.error(f"Error in main: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())