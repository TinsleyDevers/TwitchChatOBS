"""
Settings tab for the Twitch Tracker application.
"""
import os
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox, filedialog
from typing import Dict, Any
import logging

from core.tracker import TwitchTracker

logger = logging.getLogger("TwitchTracker.SettingsTab")

class SettingsTab:
    """Settings tab for configuring application settings."""
    
    def __init__(self, notebook: ttk.Notebook, tracker: TwitchTracker, colors: Dict[str, str]):
        """
        Initialize the settings tab.
        
        Args:
            notebook: Parent notebook
            tracker: TwitchTracker instance
            colors: Dictionary of UI colors
        """
        self.tracker = tracker
        self.colors = colors
        
        # Create main frame
        self.frame = ttk.Frame(notebook)
        
        # Create scrollable frame for all settings
        self.canvas = tk.Canvas(self.frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Initialize variables from tracker configuration
        self.load_variables_from_config()
        
        # Add all settings sections
        self._create_twitch_settings()
        self._create_obs_settings()
        self._create_tts_settings()
        self._create_ui_settings()
        self._create_overlay_settings()
        self._create_combo_settings()
        
        # Add save button
        save_button = ttk.Button(self.scrollable_frame, text="Save Settings", command=self.save_settings)
        save_button.pack(pady=10)
        
        # Add test connection buttons
        test_frame = ttk.Frame(self.scrollable_frame)
        test_frame.pack(pady=10)
        
        ttk.Button(test_frame, text="Test Twitch Connection", command=self.test_twitch_connection).pack(side='left', padx=5)
        ttk.Button(test_frame, text="Test OBS Connection", command=self.test_obs_connection).pack(side='left', padx=5)
        ttk.Button(test_frame, text="Test TTS", command=self.test_tts).pack(side='left', padx=5)
        
        # Add mouse wheel scrolling
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def load_variables_from_config(self):
        """Load variables from tracker configuration."""
        logger.debug("Loading variables from config")
        # Ensure all required sections exist
        for section in ['Twitch', 'OBS', 'TTS', 'UI', 'Overlay', 'General']:
            if section not in self.tracker.config:
                logger.info(f"Creating missing config section: {section}")
                self.tracker.config[section] = {}
                
        # Twitch settings
        self.nick_var = tk.StringVar(value=self.tracker.config.get('Twitch', 'nickname', fallback=''))
        self.token_var = tk.StringVar(value=self.tracker.config.get('Twitch', 'token', fallback=''))
        self.channel_var = tk.StringVar(value=self.tracker.config.get('Twitch', 'channel', fallback=''))
        self.channel_id_var = tk.StringVar(value=self.tracker.config.get('Twitch', 'channel_id', fallback=''))
        
        # OBS settings
        self.obs_host_var = tk.StringVar(value=self.tracker.config.get('OBS', 'host', fallback='localhost'))
        self.obs_port_var = tk.StringVar(value=self.tracker.config.get('OBS', 'port', fallback='4444'))
        self.obs_password_var = tk.StringVar(value=self.tracker.config.get('OBS', 'password', fallback=''))
        self.obs_source_var = tk.StringVar(value=self.tracker.config.get('OBS', 'text_source', fallback='ChatTracker'))
        
        # TTS settings
        self.tts_enabled_var = tk.BooleanVar(value=self.tracker.config.getboolean('TTS', 'enabled', fallback=True))
        self.tts_rate_var = tk.StringVar(value=self.tracker.config.get('TTS', 'rate', fallback='150'))
        self.tts_volume_var = tk.StringVar(value=self.tracker.config.get('TTS', 'volume', fallback='0.8'))
        
        # UI settings
        self.ui_theme_var = tk.StringVar(value=self.tracker.config.get('UI', 'theme', fallback='dark'))
        self.ui_accent_var = tk.StringVar(value=self.tracker.config.get('UI', 'accent_color', fallback='#5a32a8'))
        
        # Overlay settings
        self.overlay_position_var = tk.StringVar(value=self.tracker.config.get('Overlay', 'position', fallback='bottom-left'))
        self.overlay_scale_var = tk.StringVar(value=self.tracker.config.get('Overlay', 'scale', fallback='1.0'))
        self.overlay_font_var = tk.StringVar(value=self.tracker.config.get('Overlay', 'font', fallback='Arial'))
        
        # Combo settings
        self.default_combo_timeout_var = tk.StringVar(value=self.tracker.config.get('General', 'default_combo_timeout', fallback='10'))
        self.default_display_time_var = tk.StringVar(value=self.tracker.config.get('General', 'default_display_time', fallback='5'))
        self.min_combo_count_var = tk.StringVar(value=self.tracker.config.get('General', 'min_combo_count', fallback='1'))
        self.allow_multiple_var = tk.BooleanVar(value=self.tracker.config.getboolean('General', 'allow_multiple_from_user', fallback=True))
        
        logger.debug("Variables loaded from config")
    
    def _create_twitch_settings(self):
        """Create Twitch settings section."""
        twitch_frame = ttk.LabelFrame(self.scrollable_frame, text="Twitch Settings")
        twitch_frame.pack(fill='x', padx=10, pady=5)
        
        # Grid layout for this section
        twitch_grid = ttk.Frame(twitch_frame)
        twitch_grid.pack(fill='x', padx=10, pady=10)
        
        # Bot username
        ttk.Label(twitch_grid, text="Bot Username:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(twitch_grid, textvariable=self.nick_var).grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        # OAuth token
        ttk.Label(twitch_grid, text="OAuth Token:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        token_entry = ttk.Entry(twitch_grid, textvariable=self.token_var, show='*')
        token_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        
        # Channel
        ttk.Label(twitch_grid, text="Channel:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(twitch_grid, textvariable=self.channel_var).grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        
        # Channel ID
        ttk.Label(twitch_grid, text="Channel ID:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(twitch_grid, textvariable=self.channel_id_var).grid(row=3, column=1, sticky='ew', padx=5, pady=5)
        
        # Help info
        help_text = "Channel ID is needed for third-party emotes (BTTV, FFZ, 7TV).\nOAuth token can be obtained from https://twitchapps.com/tmi/"
        help_label = ttk.Label(twitch_grid, text=help_text, wraplength=300, justify='left')
        help_label.grid(row=4, column=0, columnspan=2, sticky='w', padx=5, pady=5)
        
        # Set column weights
        twitch_grid.columnconfigure(1, weight=1)
    
    def _create_obs_settings(self):
        """Create OBS settings section."""
        obs_frame = ttk.LabelFrame(self.scrollable_frame, text="OBS Settings")
        obs_frame.pack(fill='x', padx=10, pady=5)
        
        # Grid layout for this section
        obs_grid = ttk.Frame(obs_frame)
        obs_grid.pack(fill='x', padx=10, pady=10)
        
        # Host
        ttk.Label(obs_grid, text="Host:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(obs_grid, textvariable=self.obs_host_var).grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        # Port
        ttk.Label(obs_grid, text="Port:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(obs_grid, textvariable=self.obs_port_var).grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        
        # Password
        ttk.Label(obs_grid, text="Password:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(obs_grid, textvariable=self.obs_password_var, show='*').grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        
        # Text source
        ttk.Label(obs_grid, text="Text Source:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(obs_grid, textvariable=self.obs_source_var).grid(row=3, column=1, sticky='ew', padx=5, pady=5)
        
        # Help info
        help_text = "Enable WebSocket server in OBS: Tools > WebSocket Server Settings.\nThe Text Source should match the name of a text source in your OBS scene."
        help_label = ttk.Label(obs_grid, text=help_text, wraplength=300, justify='left')
        help_label.grid(row=4, column=0, columnspan=2, sticky='w', padx=5, pady=5)
        
        # Set column weights
        obs_grid.columnconfigure(1, weight=1)
    
    def _create_tts_settings(self):
        """Create TTS settings section."""
        tts_frame = ttk.LabelFrame(self.scrollable_frame, text="TTS Settings")
        tts_frame.pack(fill='x', padx=10, pady=5)
        
        # Grid layout for this section
        tts_grid = ttk.Frame(tts_frame)
        tts_grid.pack(fill='x', padx=10, pady=10)
        
        # Enable TTS
        ttk.Checkbutton(tts_grid, text="Enable Text-to-Speech", variable=self.tts_enabled_var).grid(
            row=0, column=0, columnspan=2, sticky='w', padx=5, pady=5)
        
        # Speaking rate
        ttk.Label(tts_grid, text="Speaking Rate (100-300):").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        ttk.Spinbox(tts_grid, from_=100, to=300, textvariable=self.tts_rate_var).grid(
            row=1, column=1, sticky='ew', padx=5, pady=5)
        
        # Volume
        ttk.Label(tts_grid, text="Volume (0.0-1.0):").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        volume_spin = ttk.Spinbox(tts_grid, from_=0.0, to=1.0, increment=0.1, textvariable=self.tts_volume_var)
        volume_spin.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        
        # Help info
        help_text = "TTS will speak non-emote words and combo counts.\nLower rates are slower, higher rates are faster."
        help_label = ttk.Label(tts_grid, text=help_text, wraplength=300, justify='left')
        help_label.grid(row=3, column=0, columnspan=2, sticky='w', padx=5, pady=5)
        
        # Set column weights
        tts_grid.columnconfigure(1, weight=1)
    
    def _create_ui_settings(self):
        """Create UI settings section."""
        ui_frame = ttk.LabelFrame(self.scrollable_frame, text="UI Settings")
        ui_frame.pack(fill='x', padx=10, pady=5)
        
        # Grid layout for this section
        ui_grid = ttk.Frame(ui_frame)
        ui_grid.pack(fill='x', padx=10, pady=10)
        
        # Theme
        ttk.Label(ui_grid, text="Theme:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        theme_combo = ttk.Combobox(ui_grid, textvariable=self.ui_theme_var, state='readonly')
        theme_combo['values'] = ('dark', 'light')
        theme_combo.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        # Accent color
        ttk.Label(ui_grid, text="Accent Color:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        color_frame = ttk.Frame(ui_grid)
        color_frame.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        
        color_entry = ttk.Entry(color_frame, textvariable=self.ui_accent_var)
        color_entry.pack(side='left', fill='x', expand=True)
        
        def choose_color():
            color = colorchooser.askcolor(initialcolor=self.ui_accent_var.get())[1]
            if color:
                self.ui_accent_var.set(color)
        
        color_button = ttk.Button(color_frame, text="Pick", command=choose_color)
        color_button.pack(side='right', padx=2)
        
        # Help info
        help_text = "Theme changes require restarting the application to take full effect."
        help_label = ttk.Label(ui_grid, text=help_text, wraplength=300, justify='left')
        help_label.grid(row=2, column=0, columnspan=2, sticky='w', padx=5, pady=5)
        
        # Set column weights
        ui_grid.columnconfigure(1, weight=1)
    
    def _create_overlay_settings(self):
        """Create overlay settings section."""
        overlay_frame = ttk.LabelFrame(self.scrollable_frame, text="Overlay Settings")
        overlay_frame.pack(fill='x', padx=10, pady=5)
        
        # Grid layout for this section
        overlay_grid = ttk.Frame(overlay_frame)
        overlay_grid.pack(fill='x', padx=10, pady=10)
        
        # Position
        ttk.Label(overlay_grid, text="Position:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        position_combo = ttk.Combobox(overlay_grid, textvariable=self.overlay_position_var, state='readonly')
        position_combo['values'] = ('top-left', 'top-right', 'bottom-left', 'bottom-right')
        position_combo.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        # Scale
        ttk.Label(overlay_grid, text="Scale (0.5-2.0):").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        scale_spin = ttk.Spinbox(overlay_grid, from_=0.5, to=2.0, increment=0.1, textvariable=self.overlay_scale_var)
        scale_spin.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        
        # Font
        ttk.Label(overlay_grid, text="Font:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        font_combo = ttk.Combobox(overlay_grid, textvariable=self.overlay_font_var)
        font_combo['values'] = ('Arial', 'Verdana', 'Helvetica', 'Times New Roman', 'Comic Sans MS', 'Impact', 'Courier New')
        font_combo.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        
        # Overlay file path
        ttk.Label(overlay_grid, text="Overlay File:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        overlay_path = os.path.join(self.tracker.base_dir, 'static', 'overlay.html')
        overlay_path_var = tk.StringVar(value=overlay_path)
        overlay_entry = ttk.Entry(overlay_grid, textvariable=overlay_path_var, state='readonly')
        overlay_entry.grid(row=3, column=1, sticky='ew', padx=5, pady=5)
        
        def open_folder():
            path = os.path.dirname(overlay_path)
            try:
                if os.path.exists(path):
                    os.startfile(path)
                else:
                    messagebox.showwarning("Path not found", f"The folder {path} does not exist yet.")
            except Exception as e:
                logger.error(f"Error opening folder: {e}")
                messagebox.showerror("Error", f"Could not open folder: {e}")
        
        open_button = ttk.Button(overlay_grid, text="Open Folder", command=open_folder)
        open_button.grid(row=3, column=2, padx=5, pady=5)
        
        # Help info
        help_text = "Add the overlay.html file to OBS as a Browser Source.\nScale affects the size of emotes and text in the overlay."
        help_label = ttk.Label(overlay_grid, text=help_text, wraplength=300, justify='left')
        help_label.grid(row=4, column=0, columnspan=3, sticky='w', padx=5, pady=5)
        
        # Set column weights
        overlay_grid.columnconfigure(1, weight=1)
    
    def _create_combo_settings(self):
        """Create combo settings section."""
        combo_frame = ttk.LabelFrame(self.scrollable_frame, text="Combo Settings")
        combo_frame.pack(fill='x', padx=10, pady=5)
        
        # Grid layout for this section
        combo_grid = ttk.Frame(combo_frame)
        combo_grid.pack(fill='x', padx=10, pady=10)
        
        # Default combo timeout
        ttk.Label(combo_grid, text="Default Combo Timeout (seconds):").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        timeout_spin = ttk.Spinbox(combo_grid, from_=1, to=60, textvariable=self.default_combo_timeout_var)
        timeout_spin.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        # Default display time
        ttk.Label(combo_grid, text="Default Display Time (seconds):").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        display_spin = ttk.Spinbox(combo_grid, from_=1, to=60, textvariable=self.default_display_time_var)
        display_spin.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        
        # Minimum combo count for display
        ttk.Label(combo_grid, text="Minimum Combo Count to Display:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        min_combo_spin = ttk.Spinbox(combo_grid, from_=1, to=20, textvariable=self.min_combo_count_var)
        min_combo_spin.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        
        # Minimum word length to track
        ttk.Label(combo_grid, text="Minimum Word Length to Track:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.min_word_length_var = tk.StringVar(value=self.tracker.config.get('General', 'min_word_length', fallback='2'))
        min_word_length_spin = ttk.Spinbox(combo_grid, from_=1, to=10, textvariable=self.min_word_length_var)
        min_word_length_spin.grid(row=3, column=1, sticky='ew', padx=5, pady=5)
        
        # Maximum words per message to process
        ttk.Label(combo_grid, text="Maximum Words Per Message:").grid(row=4, column=0, sticky='w', padx=5, pady=5)
        self.max_words_per_message_var = tk.StringVar(value=self.tracker.config.get('General', 'max_words_per_message', fallback='1'))
        max_words_spin = ttk.Spinbox(combo_grid, from_=1, to=20, textvariable=self.max_words_per_message_var)
        max_words_spin.grid(row=4, column=1, sticky='ew', padx=5, pady=5)
        
        # Allow multiple from user
        ttk.Checkbutton(combo_grid, text="Allow multiple contributions from same user", 
                       variable=self.allow_multiple_var).grid(row=5, column=0, columnspan=2, sticky='w', padx=5, pady=5)
        
        # Use local emotes toggle
        self.use_local_emotes_var = tk.BooleanVar(value=self.tracker.config.getboolean('General', 'use_local_emotes', fallback=True))
        ttk.Checkbutton(combo_grid, text="Use downloaded emote images", 
                       variable=self.use_local_emotes_var).grid(row=6, column=0, columnspan=2, sticky='w', padx=5, pady=5)
        
        # Help info
        help_text = "Combo Timeout: Maximum time between occurrences to count as a combo\nDisplay Time: How long to show each item in the overlay\nMinimum Combo: Minimum combo count before showing in overlay\nMinimum Word Length: Shortest word to track (except emotes)\nMaximum Words: Process up to this many words from a message"
        help_label = ttk.Label(combo_grid, text=help_text, wraplength=300, justify='left')
        help_label.grid(row=7, column=0, columnspan=2, sticky='w', padx=5, pady=5)
        
        # Set column weights
        combo_grid.columnconfigure(1, weight=1)
    
    def save_settings(self):
        """Save settings to configuration."""
        try:
            logger.info("Starting to save settings")
            
            # Validate input values
            # Port should be a number
            try:
                port = int(self.obs_port_var.get())
                logger.debug(f"OBS port validated: {port}")
            except ValueError:
                messagebox.showerror("Invalid Input", "OBS port must be a number")
                logger.error("Validation error: OBS port is not a number")
                return
                
            # TTS rate should be a number
            try:
                rate = int(self.tts_rate_var.get())
                if not (100 <= rate <= 300):
                    messagebox.showerror("Invalid Input", "TTS rate must be between 100 and 300")
                    logger.error(f"Validation error: TTS rate out of range: {rate}")
                    return
                logger.debug(f"TTS rate validated: {rate}")
            except ValueError:
                messagebox.showerror("Invalid Input", "TTS rate must be a number")
                logger.error("Validation error: TTS rate is not a number")
                return
                
            # TTS volume should be a float
            try:
                volume = float(self.tts_volume_var.get())
                if not (0.0 <= volume <= 1.0):
                    messagebox.showerror("Invalid Input", "TTS volume must be between 0.0 and 1.0")
                    logger.error(f"Validation error: TTS volume out of range: {volume}")
                    return
                logger.debug(f"TTS volume validated: {volume}")
            except ValueError:
                messagebox.showerror("Invalid Input", "TTS volume must be a number")
                logger.error("Validation error: TTS volume is not a number")
                return
                
            # Scale should be a float
            try:
                scale = float(self.overlay_scale_var.get())
                if not (0.5 <= scale <= 2.0):
                    messagebox.showerror("Invalid Input", "Overlay scale must be between 0.5 and 2.0")
                    logger.error(f"Validation error: Overlay scale out of range: {scale}")
                    return
                logger.debug(f"Overlay scale validated: {scale}")
            except ValueError:
                messagebox.showerror("Invalid Input", "Overlay scale must be a number")
                logger.error("Validation error: Overlay scale is not a number")
                return

            # Min combo count should be a positive integer
            try:
                min_combo = int(self.min_combo_count_var.get())
                if min_combo < 1:
                    messagebox.showerror("Invalid Input", "Minimum combo count must be at least 1")
                    logger.error(f"Validation error: Min combo count too low: {min_combo}")
                    return
                logger.debug(f"Min combo count validated: {min_combo}")
            except ValueError:
                messagebox.showerror("Invalid Input", "Minimum combo count must be a number")
                logger.error("Validation error: Min combo count is not a number")
                return
            
            # Ensure all config sections exist
            for section in ['Twitch', 'OBS', 'TTS', 'UI', 'Overlay', 'General']:
                if section not in self.tracker.config:
                    self.tracker.config[section] = {}
                    logger.info(f"Created missing config section: {section}")
            
            # Update Twitch settings
            logger.debug("Updating Twitch settings")
            self.tracker.config['Twitch']['nickname'] = self.nick_var.get()
            self.tracker.config['Twitch']['token'] = self.token_var.get()
            self.tracker.config['Twitch']['channel'] = self.channel_var.get()
            self.tracker.config['Twitch']['channel_id'] = self.channel_id_var.get()
            
            # Update OBS settings
            logger.debug("Updating OBS settings")
            self.tracker.config['OBS']['host'] = self.obs_host_var.get()
            self.tracker.config['OBS']['port'] = self.obs_port_var.get()
            self.tracker.config['OBS']['password'] = self.obs_password_var.get()
            self.tracker.config['OBS']['text_source'] = self.obs_source_var.get()
            
            # Update TTS settings
            logger.debug("Updating TTS settings")
            self.tracker.config['TTS']['enabled'] = str(self.tts_enabled_var.get()).lower()
            self.tracker.config['TTS']['rate'] = self.tts_rate_var.get()
            self.tracker.config['TTS']['volume'] = self.tts_volume_var.get()
            
            # Update UI settings
            logger.debug("Updating UI settings")
            self.tracker.config['UI']['theme'] = self.ui_theme_var.get()
            self.tracker.config['UI']['accent_color'] = self.ui_accent_var.get()
            
            # Update Overlay settings
            logger.debug("Updating Overlay settings")
            self.tracker.config['Overlay']['position'] = self.overlay_position_var.get()
            self.tracker.config['Overlay']['scale'] = self.overlay_scale_var.get()
            self.tracker.config['Overlay']['font'] = self.overlay_font_var.get()
            
            # Update Combo settings
            # Update Combo settings
            logger.debug("Updating Combo settings")
            self.tracker.config['General']['default_combo_timeout'] = self.default_combo_timeout_var.get()
            self.tracker.config['General']['default_display_time'] = self.default_display_time_var.get()
            self.tracker.config['General']['min_combo_count'] = self.min_combo_count_var.get()
            self.tracker.config['General']['allow_multiple_from_user'] = str(self.allow_multiple_var.get()).lower()
            self.tracker.config['General']['min_word_length'] = self.min_word_length_var.get()
            self.tracker.config['General']['max_words_per_message'] = self.max_words_per_message_var.get()
            self.tracker.config['General']['use_local_emotes'] = str(self.use_local_emotes_var.get()).lower()
            
            # Save the config to file
            logger.debug("Saving config to file")
            self.tracker.save_config()
            
            # Update tracker properties
            logger.debug("Updating tracker properties")
            self.tracker.nickname = self.nick_var.get()
            self.tracker.token = self.token_var.get()
            self.tracker.channel = self.channel_var.get()
            self.tracker.channel_id = self.channel_id_var.get()
            
            self.tracker.default_combo_timeout = int(self.default_combo_timeout_var.get())
            self.tracker.default_display_time = int(self.default_display_time_var.get())
            
            # New settings
            self.tracker.min_word_length = int(self.min_word_length_var.get())
            self.tracker.max_words_per_message = int(self.max_words_per_message_var.get())
            
            # Ensure min_combo_count exists on the tracker object
            if hasattr(self.tracker, 'min_combo_count'):
                self.tracker.min_combo_count = int(self.min_combo_count_var.get())
            else:
                # If attribute doesn't exist, add it
                logger.info("Adding min_combo_count attribute to tracker")
                setattr(self.tracker, 'min_combo_count', int(self.min_combo_count_var.get()))
                
            self.tracker.allow_multiple_from_user = self.allow_multiple_var.get()
            
            # Update component settings
            logger.debug("Updating component settings")
            self.tracker.obs_manager.host = self.obs_host_var.get()
            self.tracker.obs_manager.port = int(self.obs_port_var.get())
            self.tracker.obs_manager.password = self.obs_password_var.get()
            
            self.tracker.audio_manager.configure_tts(
                enabled=self.tts_enabled_var.get(),
                rate=int(self.tts_rate_var.get()),
                volume=float(self.tts_volume_var.get())
            )
            
            # Update overlay if it exists
            try:
                logger.debug("Updating overlay settings")
                if hasattr(self.tracker, 'overlay_manager'):
                    config = {
                        'position': self.overlay_position_var.get(),
                        'scale': float(self.overlay_scale_var.get()),
                        'font': self.overlay_font_var.get(),
                        'accentColor': self.ui_accent_var.get()
                    }
                    self.tracker.overlay_manager.update_overlay({'config': config, 'items': []})
                    logger.debug("Overlay settings updated")
            except Exception as e:
                logger.warning(f"Error updating overlay: {e}")
                # Non-critical, don't fail the settings save
            
            # Show success message
            logger.info("Settings saved successfully")
            messagebox.showinfo("Settings Saved", "Settings have been saved successfully")
                
        except Exception as e:
            import traceback
            logger.error(f"Failed to save settings: {e}")
            logger.error(traceback.format_exc())
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def test_twitch_connection(self):
        """Test the Twitch connection."""
        try:
            # Temporarily create a socket and attempt to connect
            import socket
            
            logger.info("Testing Twitch connection")
            sock = socket.socket()
            sock.settimeout(5)  # Set a timeout for the connection attempt
            
            logger.debug("Connecting to Twitch IRC")
            sock.connect(('irc.chat.twitch.tv', 6667))
            
            # Try to authenticate
            nickname = self.nick_var.get()
            token = self.token_var.get()
            
            if not nickname or not token:
                messagebox.showerror("Twitch Connection", "Username and OAuth token are required")
                logger.error("Missing username or token for Twitch test")
                sock.close()
                return
                
            logger.debug(f"Authenticating with username: {nickname}")
            sock.send(f"PASS {token}\n".encode('utf-8'))
            sock.send(f"NICK {nickname}\n".encode('utf-8'))
            
            # Wait for a response
            logger.debug("Waiting for response")
            response = sock.recv(2048).decode('utf-8')
            logger.debug(f"Response received: {response}")
            
            sock.close()
            
            if 'Welcome' in response or 'Your host is' in response:
                logger.info("Successfully connected to Twitch")
                messagebox.showinfo("Twitch Connection", "Successfully connected to Twitch!")
            elif 'Login authentication failed' in response:
                logger.error("Twitch authentication failed")
                messagebox.showerror("Twitch Connection", "Authentication failed. Please check your username and token.")
            else:
                logger.warning(f"Unexpected Twitch response: {response}")
                messagebox.showwarning("Twitch Connection", f"Connected but received unexpected response: {response}")
                
        except Exception as e:
            logger.error(f"Failed to connect to Twitch: {e}")
            messagebox.showerror("Twitch Connection", f"Failed to connect to Twitch: {e}")
    
    def test_obs_connection(self):
        """Test the OBS connection."""
        try:
            # Get the current values from the UI
            host = self.obs_host_var.get()
            port = int(self.obs_port_var.get())
            password = self.obs_password_var.get()
            
            logger.info(f"Testing OBS connection to {host}:{port}")
            
            # Create a temporary OBS connection
            from obswebsocket import obsws
            
            obs = obsws(host, port, password)
            logger.debug("Connecting to OBS")
            obs.connect()
            
            # If we get here, the connection worked
            logger.debug("Disconnecting from OBS")
            obs.disconnect()
            
            logger.info("Successfully connected to OBS")
            messagebox.showinfo("OBS Connection", "Successfully connected to OBS!")
            
        except Exception as e:
            logger.error(f"Failed to connect to OBS: {e}")
            messagebox.showerror("OBS Connection", f"Failed to connect to OBS: {e}")
    
    def test_tts(self):
        """Test the TTS engine."""
        try:
            # Get the current values from the UI
            enabled = self.tts_enabled_var.get()
            rate = int(self.tts_rate_var.get())
            volume = float(self.tts_volume_var.get())
            
            logger.info(f"Testing TTS with enabled={enabled}, rate={rate}, volume={volume}")
            
            if not enabled:
                logger.warning("TTS is disabled")
                messagebox.showwarning("TTS Test", "TTS is currently disabled. Enable it to test.")
                return
            
            # Create a temporary TTS engine with the current settings
            import pyttsx3
            
            logger.debug("Initializing TTS engine")
            engine = pyttsx3.init()
            engine.setProperty('rate', rate)
            engine.setProperty('volume', volume)
            
            # Speak a test message
            logger.debug("Speaking test message")
            engine.say("This is a test of the Text to Speech engine")
            engine.runAndWait()
            
            logger.info("TTS test completed")
            messagebox.showinfo("TTS Test", "TTS test completed")
            
        except Exception as e:
            logger.error(f"Failed to test TTS: {e}")
            messagebox.showerror("TTS Test", f"Failed to test TTS: {e}")