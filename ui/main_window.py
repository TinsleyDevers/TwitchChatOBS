"""
Main window for the Twitch Tracker application.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
from typing import Dict, Any, Optional

from core.tracker import TwitchTracker
from ui.modern_ui import ModernUI
from ui.dashboard_tab import DashboardTab
from ui.settings_tab import SettingsTab
from ui.emotes_tab import EmotesTab
from ui.stats_tab import StatsTab
from ui.about_tab import AboutTab

logger = logging.getLogger("TwitchTracker.UI")


class TwitchTrackerGUI:
    """Main GUI for the Twitch Tracker application."""
    
    def __init__(self, tracker: TwitchTracker):
        """
        Initialize the GUI.
        
        Args:
            tracker: TwitchTracker instance
        """
        self.tracker = tracker
        self.running = False
        self.update_interval = 1000  # Update interval in milliseconds
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Twitch Emote/Word Tracker")
        self.root.geometry("900x700")  # Larger initial size
        
        # Apply theme
        self.theme = tracker.config.get('UI', 'theme', fallback='dark')
        self.accent_color = tracker.config.get('UI', 'accent_color', fallback='#5a32a8')
        
        # Apply theme to UI
        if self.theme == 'dark':
            self.colors = ModernUI.apply_dark_theme(self.root)
        else:
            self.colors = ModernUI.apply_light_theme(self.root)
        
        # Create header with logo
        self._create_header()
        
        # Create control frame
        self._create_control_frame()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.dashboard_tab = DashboardTab(self.notebook, self.tracker, self.colors)
        self.settings_tab = SettingsTab(self.notebook, self.tracker, self.colors)
        self.emotes_tab = EmotesTab(self.notebook, self.tracker, self.colors)
        self.stats_tab = StatsTab(self.notebook, self.tracker, self.colors)
        self.about_tab = AboutTab(self.notebook, self.colors)
        
        # Add tabs to notebook
        self.notebook.add(self.dashboard_tab.frame, text="Dashboard")
        self.notebook.add(self.settings_tab.frame, text="Settings")
        self.notebook.add(self.emotes_tab.frame, text="Emotes & Words")
        self.notebook.add(self.stats_tab.frame, text="Stats")
        self.notebook.add(self.about_tab.frame, text="About")
        
        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Set up update timer
        self._setup_updates()
    
    def _create_header(self) -> None:
        """Create a header with logo and title."""
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill='x', padx=10, pady=10)
        
        # If logo exists, use it
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'logo.png')
        if os.path.exists(logo_path):
            try:
                from PIL import Image, ImageTk
                logo_img = Image.open(logo_path)
                logo_img = logo_img.resize((48, 48), Image.LANCZOS)
                logo_photo = ImageTk.PhotoImage(logo_img)
                logo_label = ttk.Label(header_frame, image=logo_photo)
                logo_label.image = logo_photo  # Keep a reference
                logo_label.pack(side='left', padx=5)
            except Exception as e:
                logger.error(f"Could not load logo: {e}")
        
        # Title
        title_label = ttk.Label(header_frame, text="Twitch Emote Tracker", font=("Arial", 18, "bold"))
        title_label.pack(side='left', padx=10)
    
    def _create_control_frame(self) -> None:
        """Create the control frame with status and buttons."""
        self.control_frame = ttk.Frame(self.root)
        self.control_frame.pack(fill='x', padx=10, pady=5)
        
        self.status_label = ttk.Label(self.control_frame, text="Status: Stopped", font=("Arial", 10))
        self.status_label.pack(side='left', padx=5)
        
        # Button frame for alignment
        button_frame = ttk.Frame(self.control_frame)
        button_frame.pack(side='right', padx=5)
        
        self.start_button = ttk.Button(button_frame, text="Start Tracker", command=self.toggle_tracker)
        self.start_button.pack(side='left', padx=5)
        
        self.reload_button = ttk.Button(button_frame, text="Reload Emotes", command=self.reload_emotes)
        self.reload_button.pack(side='left', padx=5)
    
    def _setup_updates(self) -> None:
        """Set up periodic updates for UI elements."""
        self.update_ui()
        
        # Schedule next update
        self.root.after(self.update_interval, self._setup_updates)
    
    def update_ui(self) -> None:
        """Update all UI elements."""
        # Update dashboard tab
        if hasattr(self, 'dashboard_tab'):
            self.dashboard_tab.update()
        
        # Update stats tab
        if hasattr(self, 'stats_tab'):
            self.stats_tab.update()
        
        # Update status label with current state
        if self.running:
            self.status_label.config(text="Status: Running")
        else:
            self.status_label.config(text="Status: Stopped")
    
    def toggle_tracker(self) -> None:
        """Start or stop the tracker."""
        if self.running:
            # Stop the tracker
            self.tracker.stop()
            self.running = False
            self.start_button.config(text="Start Tracker")
            self.status_label.config(text="Status: Stopped")
        else:
            # Start the tracker
            try:
                if self.tracker.start():
                    self.running = True
                    self.start_button.config(text="Stop Tracker")
                    self.status_label.config(text="Status: Running")
                else:
                    messagebox.showerror("Error", "Failed to start tracker")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start tracker: {e}")
                logger.error(f"Failed to start tracker: {e}")
    
    def reload_emotes(self) -> None:
        """Reload emotes from configuration."""
        try:
            # First reload the emotes in the tracker
            self.tracker.known_emotes = self.tracker._load_known_emotes()
            self.tracker.emote_configs = self.tracker._load_emote_configs()
            
            # Then update the emotes tab
            if hasattr(self, 'emotes_tab'):
                if self.emotes_tab.reload_emotes():
                    messagebox.showinfo("Reload Complete", "Emotes and configurations reloaded.")
                else:
                    messagebox.showwarning("Partial Reload", "Some emotes may not have loaded correctly.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reload emotes: {e}")
            logger.error(f"Failed to reload emotes: {e}")
    
    def on_close(self) -> None:
        """Handle window close event."""
        if self.running:
            confirm = messagebox.askyesno(
                "Quit", 
                "Tracker is still running. Are you sure you want to quit?"
            )
            
            if not confirm:
                return
            
            # Stop the tracker
            self.tracker.stop()
        
        self.root.destroy()
    
    def run(self) -> None:
        """Run the GUI application."""
        self.root.mainloop()