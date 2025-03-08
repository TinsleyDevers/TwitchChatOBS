"""
Dashboard tab for the Twitch Tracker application.
"""
import time
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List, Optional

from core.tracker import TwitchTracker


class DashboardTab:
    """Dashboard tab showing current activity."""
    
    def __init__(self, notebook: ttk.Notebook, tracker: TwitchTracker, colors: Dict[str, str]):
        """
        Initialize the dashboard tab.
        
        Args:
            notebook: Parent notebook
            tracker: TwitchTracker instance
            colors: Dictionary of UI colors
        """
        self.tracker = tracker
        self.colors = colors
        
        # Create main frame
        self.frame = ttk.Frame(notebook)
        
        # Create current combos frame
        self._create_combos_frame()
        
        # Create stats summary frame
        self._create_stats_frame()
        
        # Initial update
        self.update()
    
    def _create_combos_frame(self) -> None:
        """Create the combos display frame."""
        combos_frame = ttk.LabelFrame(self.frame, text="Current Combos")
        combos_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Treeview for combos
        columns = ('emote', 'count', 'contributors', 'time_left')
        self.combo_tree = ttk.Treeview(combos_frame, columns=columns, show='headings')
        
        # Define headings
        self.combo_tree.heading('emote', text='Emote/Word')
        self.combo_tree.heading('count', text='Count')
        self.combo_tree.heading('contributors', text='Contributors')
        self.combo_tree.heading('time_left', text='Time Left')
        
        # Define columns
        self.combo_tree.column('emote', width=200)
        self.combo_tree.column('count', width=80)
        self.combo_tree.column('contributors', width=300)
        self.combo_tree.column('time_left', width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(combos_frame, orient="vertical", command=self.combo_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.combo_tree.configure(yscrollcommand=scrollbar.set)
        self.combo_tree.pack(side='left', fill='both', expand=True)
        
        # Add right-click menu for combo actions
        self.combo_context_menu = tk.Menu(self.frame, tearoff=0)
        self.combo_context_menu.add_command(label="Clear Combo", command=self.clear_selected_combo)
        
        # Bind right-click to show context menu
        self.combo_tree.bind("<Button-3>", self.show_combo_context_menu)
        
        # Button frame
        button_frame = ttk.Frame(combos_frame)
        button_frame.pack(fill='x', pady=5)
        
        ttk.Button(button_frame, text="Clear All Combos", command=self.clear_all_combos).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Refresh", command=self.update).pack(side='left', padx=5)
    
    def _create_stats_frame(self) -> None:
        """Create the stats summary frame."""
        stats_frame = ttk.LabelFrame(self.frame, text="Stats Summary")
        stats_frame.pack(fill='x', padx=10, pady=10)
        
        # Stats labels
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill='x', padx=10, pady=10)
        
        # Total emotes processed
        ttk.Label(stats_grid, text="Total Emotes:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.total_emotes_var = tk.StringVar(value="0")
        ttk.Label(stats_grid, textvariable=self.total_emotes_var).grid(row=0, column=1, sticky='w', padx=5, pady=5)
        
        # Top emote
        ttk.Label(stats_grid, text="Top Emote:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.top_emote_var = tk.StringVar(value="None")
        ttk.Label(stats_grid, textvariable=self.top_emote_var).grid(row=1, column=1, sticky='w', padx=5, pady=5)
        
        # Largest combo
        ttk.Label(stats_grid, text="Largest Combo:").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.largest_combo_var = tk.StringVar(value="0")
        ttk.Label(stats_grid, textvariable=self.largest_combo_var).grid(row=0, column=3, sticky='w', padx=5, pady=5)
        
        # Total messages
        ttk.Label(stats_grid, text="Total Words:").grid(row=1, column=2, sticky='w', padx=5, pady=5)
        self.total_words_var = tk.StringVar(value="0")
        ttk.Label(stats_grid, textvariable=self.total_words_var).grid(row=1, column=3, sticky='w', padx=5, pady=5)
    
    def show_combo_context_menu(self, event) -> None:
        """Show context menu for a combo item."""
        # Only show menu if an item is selected
        item = self.combo_tree.identify_row(event.y)
        if item:
            self.combo_tree.selection_set(item)
            self.combo_context_menu.post(event.x_root, event.y_root)
    
    def clear_selected_combo(self) -> None:
        """Clear the selected combo."""
        selection = self.combo_tree.selection()
        if not selection:
            return
            
        # Get emote/word text from the item
        emote_text = self.combo_tree.item(selection[0], 'values')[0]
        
        try:
            # Call tracker method to clear the combo
            if self.tracker.combo_manager.clear_combo(emote_text):
                # Update UI
                self.update()
                
                # Update overlay
                self.tracker.update_overlay()
        except Exception as e:
            import logging
            logging.getLogger("TwitchTracker.UI").error(f"Error clearing combo: {e}")
            messagebox.showerror("Error", f"Failed to clear combo: {e}")
    
    def clear_all_combos(self) -> None:
        """Clear all active combos."""
        if messagebox.askyesno("Clear All Combos", "Are you sure you want to clear all active combos?"):
            try:
                # Call tracker method to clear all combos
                self.tracker.combo_manager.clear_all_combos()
                
                # Update UI
                self.update()
                
                # Update overlay
                self.tracker.update_overlay()
            except Exception as e:
                import logging
                logging.getLogger("TwitchTracker.UI").error(f"Error clearing all combos: {e}")
                messagebox.showerror("Error", f"Failed to clear all combos: {e}")
    
    def update(self) -> None:
        """Update the dashboard display with current data."""
        try:
            # Get current stats
            stats = self.tracker.get_stats()
            
            # Update combos tree
            for item in self.combo_tree.get_children():
                self.combo_tree.delete(item)
            
            now = time.time()
            for combo in stats.get("active_combos", []):
                time_left = max(0, int((combo.get("expires", 0) / 1000) - now))
                contributors = ", ".join(combo.get("contributors", [])[:5])
                if len(combo.get("contributors", [])) > 5:
                    contributors += f" +{len(combo.get('contributors', [])) - 5} more"
                
                self.combo_tree.insert('', 'end', values=(
                    combo.get("text", ""), 
                    combo.get("combo", 0), 
                    contributors, 
                    f"{time_left}s"
                ))
            
            # Update stats summary
            self.total_emotes_var.set(str(stats.get("total_emotes", 0)))
            
            # Determine total words
            word_counts = stats.get("word_counts", {})
            total_words = sum(count for word, count in word_counts.items() 
                             if word not in self.tracker.known_emotes)
            self.total_words_var.set(str(total_words))
            
            # Get top emote
            top_emote = stats.get("top_emote")
            top_count = stats.get("top_emote_count", 0)
            if top_emote:
                self.top_emote_var.set(f"{top_emote} ({top_count})")
            else:
                self.top_emote_var.set("None")
            
            # Get largest combo
            self.largest_combo_var.set(str(stats.get("largest_combo", 0)))
            
        except Exception as e:
            import logging
            logging.getLogger("TwitchTracker.UI").error(f"Error updating dashboard: {e}")