# ui/about_tab.py
"""
About tab for the Twitch Tracker application.
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any


class AboutTab:
    """About tab showing information and credits."""
    
    def __init__(self, notebook: ttk.Notebook, colors: Dict[str, str]):
        """
        Initialize the about tab.
        
        Args:
            notebook: Parent notebook
            colors: Dictionary of UI colors
        """
        self.colors = colors
        
        # Create main frame
        self.frame = ttk.Frame(notebook)
        
        # App name and version
        app_name = ttk.Label(self.frame, text="Twitch Emote Tracker", font=("Arial", 16, "bold"))
        app_name.pack(pady=(20, 5))
        
        version = ttk.Label(self.frame, text="Version 2.0")
        version.pack(pady=5)
        
        # Description
        description = ttk.Label(self.frame, text="A tool to track and display emotes and words from Twitch chat.\n"
                              "Supports custom emotes from BTTV, FrankerFaceZ, and 7TV.", 
                              wraplength=500, justify="center")
        description.pack(pady=10)
        
        # Features
        features_frame = ttk.LabelFrame(self.frame, text="Features")
        features_frame.pack(fill='x', padx=20, pady=10)
        
        features_text = "• Track emotes and words from Twitch chat\n"\
                      "• Support for Twitch, BTTV, FFZ, and 7TV emotes\n"\
                      "• Customizable display and animations\n"\
                      "• Text-to-speech support\n"\
                      "• OBS integration via websocket\n"\
                      "• Combo counter for repeated emotes"
        
        features_label = ttk.Label(features_frame, text=features_text, justify="left", wraplength=500)
        features_label.pack(padx=10, pady=10)
        
        # Credits
        credits_frame = ttk.LabelFrame(self.frame, text="Credits")
        credits_frame.pack(fill='x', padx=20, pady=10)
        
        credits_text = "This application uses the following libraries:\n"\
                     "• Python-OBS-Websocket\n"\
                     "• pyttsx3 for TTS\n"\
                     "• Pygame for audio\n"\
                     "• Tkinter for GUI"
        
        credits_label = ttk.Label(credits_frame, text=credits_text, justify="left", wraplength=500)
        credits_label.pack(padx=10, pady=10)