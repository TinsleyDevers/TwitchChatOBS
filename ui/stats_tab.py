"""
Stats tab for the Twitch Tracker application.
"""
import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Any, List, Tuple

from core.tracker import TwitchTracker


class StatsTab:
    """Stats tab showing word/emote counts."""
    
    def __init__(self, notebook: ttk.Notebook, tracker: TwitchTracker, colors: Dict[str, str]):
        """
        Initialize the stats tab.
        
        Args:
            notebook: Parent notebook
            tracker: TwitchTracker instance
            colors: Dictionary of UI colors
        """
        self.tracker = tracker
        self.colors = colors
        
        # Create main frame
        self.frame = ttk.Frame(notebook)
        
        # Top frame for controls
        controls_frame = ttk.Frame(self.frame)
        controls_frame.pack(fill='x', padx=10, pady=5)
        
        # Refresh button
        ttk.Button(controls_frame, text="Refresh Stats", command=self.refresh_stats).pack(side='left', padx=5)
        
        # Clear button
        ttk.Button(controls_frame, text="Clear Stats", command=self.clear_stats).pack(side='left', padx=5)
        
        # Export button
        ttk.Button(controls_frame, text="Export Stats", command=self.export_stats).pack(side='left', padx=5)
        
        # Search and filter controls
        search_frame = ttk.Frame(controls_frame)
        search_frame.pack(side='right', padx=5)
        
        ttk.Label(search_frame, text="Filter:").pack(side='left', padx=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side='left', padx=5)
        search_entry.bind("<KeyRelease>", lambda e: self.refresh_stats())
        
        # Filter type dropdown
        ttk.Label(search_frame, text="Type:").pack(side='left', padx=5)
        self.filter_type_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(search_frame, textvariable=self.filter_type_var, width=10, state='readonly')
        filter_combo['values'] = ('All', 'Emotes', 'Words')
        filter_combo.pack(side='left', padx=5)
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_stats())
        
        # Sort controls
        sort_frame = ttk.Frame(controls_frame)
        sort_frame.pack(side='right', padx=20)
        
        ttk.Label(sort_frame, text="Sort by:").pack(side='left', padx=5)
        self.sort_by_var = tk.StringVar(value="Count")
        sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_by_var, width=10, state='readonly')
        sort_combo['values'] = ('Count', 'Name')
        sort_combo.pack(side='left', padx=5)
        sort_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_stats())
        
        self.sort_dir_var = tk.StringVar(value="Descending")
        sort_dir_combo = ttk.Combobox(sort_frame, textvariable=self.sort_dir_var, width=10, state='readonly')
        sort_dir_combo['values'] = ('Ascending', 'Descending')
        sort_dir_combo.pack(side='left', padx=5)
        sort_dir_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_stats())
        
        # Frame for treeview
        tree_frame = ttk.Frame(self.frame)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create treeview with scrollbar
        columns = ('item', 'count', 'type')
        self.stats_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        
        # Define headings
        self.stats_tree.heading('item', text='Word/Emote')
        self.stats_tree.heading('count', text='Count')
        self.stats_tree.heading('type', text='Type')
        
        # Define columns
        self.stats_tree.column('item', width=200)
        self.stats_tree.column('count', width=100)
        self.stats_tree.column('type', width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.stats_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.stats_tree.configure(yscrollcommand=scrollbar.set)
        self.stats_tree.pack(side='left', fill='both', expand=True)
        
        # Status bar for totals
        status_frame = ttk.Frame(self.frame)
        status_frame.pack(fill='x', padx=10, pady=5)
        
        self.total_label = ttk.Label(status_frame, text="Total Items: 0   |   Total Emotes: 0   |   Total Words: 0")
        self.total_label.pack(side='left', padx=5)
        
        # Enable sorting when clicking on headers
        for col in columns:
            self.stats_tree.heading(col, command=lambda _col=col: self.treeview_sort_column(_col, False))
        
        # Initial population
        self.refresh_stats()
    
    def treeview_sort_column(self, col, reverse):
        """Sort treeview column when clicked."""
        l = [(self.stats_tree.set(k, col), k) for k in self.stats_tree.get_children('')]
        
        try:
            # Try to convert to int for numeric sorting if possible
            if col == 'count':
                l = [(int(count), k) for count, k in l]
        except:
            pass
            
        l.sort(reverse=reverse)
        
        # Rearrange items according to sorted positions
        for index, (val, k) in enumerate(l):
            self.stats_tree.move(k, '', index)
        
        # Reverse sort next time
        self.stats_tree.heading(col, command=lambda: self.treeview_sort_column(col, not reverse))
    
    def refresh_stats(self):
        """Refresh the stats display."""
        # Clear current items
        for item in self.stats_tree.get_children():
            self.stats_tree.delete(item)
        
        # Get current stats from tracker
        stats = self.tracker.get_stats()
        word_counts = stats.get("word_counts", {})
        
        # Apply filters
        filter_text = self.search_var.get().lower()
        filter_type = self.filter_type_var.get()
        
        # Process each word/emote
        filtered_items = []
        for word, count in word_counts.items():
            # Apply text filter
            if filter_text and filter_text not in word.lower():
                continue
                
            # Determine type
            is_emote = word in self.tracker.known_emotes
            item_type = "Emote" if is_emote else "Word"
            
            # Apply type filter
            if filter_type == "Emotes" and not is_emote:
                continue
            if filter_type == "Words" and is_emote:
                continue
                
            # Add to filtered items
            filtered_items.append((word, count, item_type))
        
        # Sort items
        sort_by = self.sort_by_var.get()
        sort_direction = self.sort_dir_var.get()
        reverse = sort_direction == "Descending"
        
        if sort_by == "Count":
            filtered_items.sort(key=lambda x: x[1], reverse=reverse)
        else:  # Sort by name
            filtered_items.sort(key=lambda x: x[0].lower(), reverse=reverse)
        
        # Add to treeview
        for word, count, item_type in filtered_items:
            self.stats_tree.insert('', 'end', values=(word, count, item_type))
        
        # Update totals
        total_items = len(filtered_items)
        total_emotes = sum(1 for _, _, t in filtered_items if t == "Emote")
        total_words = sum(1 for _, _, t in filtered_items if t == "Word")
        
        self.total_label.config(
            text=f"Total Items: {total_items}   |   Total Emotes: {total_emotes}   |   Total Words: {total_words}"
        )
    
    def clear_stats(self):
        """Clear all stats."""
        if messagebox.askyesno("Clear Stats", "Are you sure you want to clear all stats? This cannot be undone."):
            self.tracker.clear_stats()
            self.refresh_stats()
            messagebox.showinfo("Stats Cleared", "All statistics have been cleared.")
    
    def export_stats(self):
        """Export stats to CSV file."""
        file_path = filedialog.asksaveasfilename(
            title="Export Stats",
            defaultextension=".csv",
            filetypes=(("CSV Files", "*.csv"), ("All Files", "*.*"))
        )
        
        if not file_path:
            return
            
        try:
            # Get current items in the treeview (respecting filters)
            items = []
            for item_id in self.stats_tree.get_children():
                values = self.stats_tree.item(item_id, 'values')
                items.append(values)
            
            # Write to CSV
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Word/Emote', 'Count', 'Type'])
                writer.writerows(items)
            
            messagebox.showinfo("Export Successful", f"Stats exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export stats: {e}")
    
    def update(self):
        """Update the stats display (called periodically)."""
        # Only refresh if the tab is visible to avoid unnecessary processing
        if self.frame.winfo_viewable():
            self.refresh_stats()