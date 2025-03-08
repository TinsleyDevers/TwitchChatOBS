"""
Emotes tab for the Twitch Tracker application.
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox
from typing import Dict, Any, Optional, Tuple

from core.data_models import EmoteConfig
from core.tracker import TwitchTracker
from ui.modern_ui import ModernUI


class EmotesTab:
    """Emotes tab for managing emotes and words."""
    
    def __init__(self, notebook: ttk.Notebook, tracker: TwitchTracker, colors: Dict[str, str]):
        """
        Initialize the emotes tab.
        
        Args:
            notebook: Parent notebook
            tracker: TwitchTracker instance
            colors: Dictionary of UI colors
        """
        self.tracker = tracker
        self.colors = colors
        
        # Create main frame
        self.frame = ttk.Frame(notebook)
        
        # Split into left and right panes
        paned_window = ttk.PanedWindow(self.frame, orient='horizontal')
        paned_window.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left side - list of emotes/words
        self.list_frame = ttk.Frame(paned_window)
        paned_window.add(self.list_frame, weight=1)
        
        # Right side - item configuration
        self.config_frame = ttk.LabelFrame(paned_window, text="Configuration")
        paned_window.add(self.config_frame, weight=1)
        
        # Create list panel
        self._create_list_panel()
        
        # Create config panel
        self._create_config_panel()
        
        # Initial population of the list
        self.populate_list()
    
    def _create_list_panel(self):
        """Create the emotes/words list panel."""
        # Search box
        search_frame = ttk.Frame(self.list_frame)
        search_frame.pack(fill='x', pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side='left', padx=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side='left', fill='x', expand=True, padx=5)
        search_entry.bind("<KeyRelease>", lambda e: self.search_items())
        
        # Category filter
        filter_frame = ttk.Frame(self.list_frame)
        filter_frame.pack(fill='x', pady=5)
        
        self.show_emotes_var = tk.BooleanVar(value=True)
        show_emotes_cb = ttk.Checkbutton(filter_frame, text="Show Emotes", variable=self.show_emotes_var)
        show_emotes_cb.pack(side='left', padx=5)
        show_emotes_cb.configure(command=self.search_items)
        
        self.show_words_var = tk.BooleanVar(value=True)
        show_words_cb = ttk.Checkbutton(filter_frame, text="Show Words", variable=self.show_words_var)
        show_words_cb.pack(side='left', padx=5)
        show_words_cb.configure(command=self.search_items)
        
        # Listbox with scrollbar
        list_container = ttk.Frame(self.list_frame)
        list_container.pack(fill='both', expand=True)
        
        self.item_listbox = tk.Listbox(list_container, bg=self.colors['input_bg'], fg=self.colors['fg'])
        self.item_listbox.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.item_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.item_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Bind selection event
        self.item_listbox.bind('<<ListboxSelect>>', self.on_item_select)
        
        # Buttons for list management
        button_frame = ttk.Frame(self.list_frame)
        button_frame.pack(fill='x', pady=5)
        
        ttk.Button(button_frame, text="Add Emote", command=self.add_emote).pack(side='left', padx=2)
        ttk.Button(button_frame, text="Add Word", command=self.add_word).pack(side='left', padx=2)
        ttk.Button(button_frame, text="Remove", command=self.remove_item).pack(side='left', padx=2)
        ttk.Button(button_frame, text="Fetch 3rd Party", command=self.fetch_third_party).pack(side='left', padx=2)
    
    def _create_config_panel(self):
        """Create the configuration panel."""
        # Create scrollable config area
        canvas, scrollable_config = ModernUI.create_scrollable_frame(self.config_frame)
        
        ttk.Label(scrollable_config, text="Select an item from the list to configure").pack(pady=10)
        
        # Audio configuration
        audio_frame = ttk.Frame(scrollable_config)
        audio_frame.pack(fill='x', pady=5)
        
        ttk.Label(audio_frame, text="Custom Audio:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.audio_path_var = tk.StringVar()
        ttk.Entry(audio_frame, textvariable=self.audio_path_var).grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        ttk.Button(audio_frame, text="Browse...", command=self.browse_audio).grid(row=0, column=2, padx=5, pady=5)
        
        # Preview button
        ttk.Button(audio_frame, text="Preview Audio", command=self.preview_audio).grid(row=1, column=1, padx=5, pady=5)
        
        # Display settings
        display_frame = ttk.LabelFrame(scrollable_config, text="Display Settings")
        display_frame.pack(fill='x', pady=10, padx=5)
        
        ttk.Label(display_frame, text="Color:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.color_var = tk.StringVar(value="#FFFFFF")
        color_frame = ttk.Frame(display_frame)
        color_frame.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        color_entry = ttk.Entry(color_frame, textvariable=self.color_var)
        color_entry.pack(side='left', fill='x', expand=True)
        
        color_button = ttk.Button(color_frame, text="Pick", command=self.pick_item_color)
        color_button.pack(side='right', padx=5)
        
        ttk.Label(display_frame, text="Font:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.font_var = tk.StringVar(value="Arial")
        font_combo = ttk.Combobox(display_frame, textvariable=self.font_var)
        font_combo['values'] = ('Arial', 'Verdana', 'Tahoma', 'Times New Roman', 'Courier New')
        font_combo.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        
        ttk.Label(display_frame, text="Size:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.size_var = tk.StringVar(value="24")
        size_spinbox = ttk.Spinbox(display_frame, from_=10, to=72, textvariable=self.size_var)
        size_spinbox.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        
        ttk.Label(display_frame, text="Animation:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.animation_var = tk.StringVar(value="bounce")
        animation_combo = ttk.Combobox(display_frame, textvariable=self.animation_var)
        animation_combo['values'] = ('bounce', 'fade', 'pulse', 'slide', 'none')
        animation_combo.grid(row=3, column=1, sticky='ew', padx=5, pady=5)
        
        # Timing settings
        timing_frame = ttk.LabelFrame(scrollable_config, text="Timing Settings")
        timing_frame.pack(fill='x', pady=10, padx=5)
        
        ttk.Label(timing_frame, text="Display Time (s):").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.display_time_var = tk.StringVar(value="5")
        display_spinbox = ttk.Spinbox(timing_frame, from_=1, to=60, textvariable=self.display_time_var)
        display_spinbox.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        ttk.Label(timing_frame, text="Combo Timeout (s):").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.combo_timeout_var = tk.StringVar(value="10")
        timeout_spinbox = ttk.Spinbox(timing_frame, from_=1, to=60, textvariable=self.combo_timeout_var)
        timeout_spinbox.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        
        # Show in overlay checkbox
        self.show_overlay_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(scrollable_config, text="Show in overlay", variable=self.show_overlay_var).pack(anchor='w', padx=5, pady=5)
        
        # Save button
        ttk.Button(scrollable_config, text="Save Item Configuration", command=self.save_item_config).pack(pady=10)
    
    def populate_list(self):
        """Populate the listbox with emotes and words."""
        self.item_listbox.delete(0, tk.END)
        
        # Add known emotes
        if self.show_emotes_var.get():
            for emote in sorted(self.tracker.known_emotes):
                self.item_listbox.insert(tk.END, f"[Emote] {emote}")
        
        # Add tracked words
        if self.show_words_var.get():
            for word, config in sorted(self.tracker.emote_configs.items()):
                if not config.is_emote:
                    self.item_listbox.insert(tk.END, f"[Word] {word}")
    
    def search_items(self):
        """Search and filter items in the list."""
        search_text = self.search_var.get().lower()
        self.item_listbox.delete(0, tk.END)
        
        # Filter emotes
        if self.show_emotes_var.get():
            for emote in sorted(self.tracker.known_emotes):
                if search_text in emote.lower():
                    self.item_listbox.insert(tk.END, f"[Emote] {emote}")
        
        # Filter words
        if self.show_words_var.get():
            for word, config in sorted(self.tracker.emote_configs.items()):
                if not config.is_emote and search_text in word.lower():
                    self.item_listbox.insert(tk.END, f"[Word] {word}")
    
    def on_item_select(self, event):
        """Handle selection of an item from the listbox."""
        if not self.item_listbox.curselection():
            return
        
        selection = self.item_listbox.get(self.item_listbox.curselection()[0])
        
        # Extract item type and name
        if selection.startswith('[Emote]'):
            item_type = 'emote'
            item_name = selection[7:].strip()
        else:
            item_type = 'word'
            item_name = selection[6:].strip()
        
        # Load configuration if exists
        if item_name in self.tracker.emote_configs:
            config = self.tracker.emote_configs[item_name]
            
            # Update UI with config values
            if config.custom_audio:
                self.audio_path_var.set(config.custom_audio)
            else:
                self.audio_path_var.set('')
            
            self.color_var.set(config.color)
            self.font_var.set(config.font)
            self.size_var.set(str(config.size))
            self.display_time_var.set(str(config.display_time))
            self.combo_timeout_var.set(str(config.combo_timeout))
            self.show_overlay_var.set(config.show_in_overlay)
            self.animation_var.set(config.animation)
        else:
            # Default values if no config exists
            self.audio_path_var.set('')
            self.color_var.set('#FFFFFF')
            self.font_var.set('Arial')
            self.size_var.set('24')
            self.display_time_var.set('5')
            self.combo_timeout_var.set('10')
            self.show_overlay_var.set(True)
            self.animation_var.set('bounce')
    
    def pick_item_color(self):
        """Open color picker for the item color."""
        color = colorchooser.askcolor(initialcolor=self.color_var.get())[1]
        if color:
            self.color_var.set(color)
    
    def browse_audio(self):
        """Browse for audio file."""
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=(
                ("Audio Files", "*.mp3 *.wav *.ogg"),
                ("All Files", "*.*")
            )
        )
        
        if file_path:
            self.audio_path_var.set(file_path)
    
    def preview_audio(self):
        """Preview the selected audio file."""
        audio_path = self.audio_path_var.get()
        if audio_path and os.path.exists(audio_path):
            self.tracker.audio_manager.play_audio_file(audio_path)
        else:
            messagebox.showwarning("Audio Preview", "No audio file selected or file not found.")
    
    def save_item_config(self):
        """Save configuration for the selected item."""
        if not self.item_listbox.curselection():
            return
        
        selection = self.item_listbox.get(self.item_listbox.curselection()[0])
        
        # Extract item type and name
        if selection.startswith('[Emote]'):
            is_emote = True
            item_name = selection[7:].strip()
        else:
            is_emote = False
            item_name = selection[6:].strip()
        
        try:
            # Create or update config
            self.tracker.emote_configs[item_name] = EmoteConfig(
                is_emote=is_emote,
                custom_audio=self.audio_path_var.get() if self.audio_path_var.get() else None,
                color=self.color_var.get(),
                font=self.font_var.get(),
                size=int(self.size_var.get()),
                display_time=int(self.display_time_var.get()),
                combo_timeout=int(self.combo_timeout_var.get()),
                show_in_overlay=self.show_overlay_var.get(),
                animation=self.animation_var.get()
            )
            
            # Save configs to file
            self.tracker.save_emote_configs()
            
            # Show confirmation
            messagebox.showinfo("Configuration Saved", f"Configuration for {item_name} has been saved.")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid numeric value: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def add_emote(self):
        """Add a new emote to the tracker."""
        emote = tk.simpledialog.askstring("Add Emote", "Enter emote name:")
        if not emote:
            return
        
        # Add to known emotes
        self.tracker.known_emotes.add(emote)
        self.tracker.save_known_emotes()
        
        # Create default config
        if emote not in self.tracker.emote_configs:
            self.tracker.emote_configs[emote] = EmoteConfig(is_emote=True)
            self.tracker.save_emote_configs()
        
        # Refresh the list
        self.populate_list()
        self.search_items()
    
    def add_word(self):
        """Add a new word to track."""
        word = tk.simpledialog.askstring("Add Word", "Enter word to track:")
        if not word:
            return
        
        # Create default config
        if word not in self.tracker.emote_configs:
            self.tracker.emote_configs[word] = EmoteConfig(is_emote=False)
            self.tracker.save_emote_configs()
        
        # Refresh the list
        self.populate_list()
        self.search_items()
    
    def remove_item(self):
        """Remove the selected item."""
        if not self.item_listbox.curselection():
            return
        
        selection = self.item_listbox.get(self.item_listbox.curselection()[0])
        
        # Extract item type and name
        if selection.startswith('[Emote]'):
            is_emote = True
            item_name = selection[7:].strip()
        else:
            is_emote = False
            item_name = selection[6:].strip()
        
        # Confirm removal
        confirm = messagebox.askyesno(
            "Confirm Removal", 
            f"Are you sure you want to remove {item_name}?"
        )
        
        if not confirm:
            return
        
        # Remove from tracking
        if is_emote:
            self.tracker.known_emotes.discard(item_name)
            self.tracker.save_known_emotes()
        
        # Remove configuration
        if item_name in self.tracker.emote_configs:
            del self.tracker.emote_configs[item_name]
            self.tracker.save_emote_configs()
        
        # Refresh the list
        self.populate_list()
        self.search_items()
    
    def fetch_third_party(self):
        """Fetch third-party emotes."""
        if not self.tracker.channel_id:
            messagebox.showwarning(
                "Channel ID Required", 
                "Please enter your Twitch Channel ID in Settings to fetch emotes."
            )
            return
        
        # Show progress dialog
        progress_window = tk.Toplevel(self.frame)
        progress_window.title("Fetching Emotes")
        progress_window.geometry("300x100")
        progress_window.transient(self.frame)
        progress_window.grab_set()
        
        ttk.Label(progress_window, text="Fetching emotes from BTTV, FFZ, and 7TV...").pack(pady=10)
        progress = ttk.Progressbar(progress_window, mode='indeterminate')
        progress.pack(fill='x', padx=20, pady=10)
        progress.start()
        
        # Function to run fetch in background
        def fetch_emotes_bg():
            try:
                import asyncio
                # Run the coroutine in the event loop
                future = asyncio.run_coroutine_threadsafe(
                    self.tracker.fetch_all_emotes(), 
                    self.tracker.loop
                )
                result = future.result(30)  # Wait up to 30 seconds
                
                # Schedule UI update back on main thread
                self.frame.after(100, lambda: finish_fetch(result))
            except Exception as e:
                import logging
                logging.getLogger("TwitchTracker.UI").error(f"Error fetching emotes: {e}")
                self.frame.after(0, lambda: progress_window.destroy())
                self.frame.after(0, lambda: messagebox.showerror("Error", f"Failed to fetch emotes: {e}"))
        
        def finish_fetch(result):
            try:
                # Refresh emote list
                self.populate_list()
                
                # Close progress window
                progress_window.destroy()
                
                # Show result
                messagebox.showinfo("Success", f"Successfully loaded {len(result)} emotes.")
            except Exception as e:
                import logging
                logging.getLogger("TwitchTracker.UI").error(f"Error updating UI after fetch: {e}")
                progress_window.destroy()
        
        # Start fetch in background
        import threading
        threading.Thread(target=fetch_emotes_bg, daemon=True).start()
    
    def reload_emotes(self):
        """Reload emotes from configuration files."""
        try:
            # Reload known emotes
            self.tracker.known_emotes = self.tracker._load_known_emotes()
            
            # Reload emote configs
            self.tracker.emote_configs = self.tracker._load_emote_configs()
            
            # Update list
            self.populate_list()
            
            return True
        except Exception as e:
            import logging
            logging.getLogger("TwitchTracker.UI").error(f"Error reloading emotes: {e}")
            return False