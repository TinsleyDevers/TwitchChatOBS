"""
Modern UI utilities for the Twitch Tracker application.
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Callable, Tuple


class ModernUI:
    """Utility class for modern UI styles and elements."""
    
    @staticmethod
    def apply_dark_theme(root: tk.Tk) -> Dict[str, str]:
        """
        Apply dark theme to tkinter window.
        
        Args:
            root: Root Tkinter window
            
        Returns:
            Dict[str, str]: Dictionary of theme colors
        """
        # Define colors
        bg_color = "#1E1E1E"
        text_color = "#FFFFFF"
        accent_color = "#5A32A8"
        accent_light = "#7D59C0"
        input_bg = "#2D2D2D"
        
        style = ttk.Style()
        style.theme_use('clam')  # Use clam theme as base
        
        # Configure common styles
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=text_color)
        style.configure('TButton', background=accent_color, foreground=text_color)
        style.map('TButton', 
                 background=[('active', accent_light), ('pressed', accent_color)],
                 foreground=[('active', text_color), ('pressed', text_color)])
        
        style.configure('TCheckbutton', background=bg_color, foreground=text_color)
        style.map('TCheckbutton', 
                 background=[('active', bg_color)],
                 foreground=[('active', text_color)])
        
        style.configure('TEntry', fieldbackground=input_bg, foreground=text_color)
        style.configure('TNotebook', background=bg_color, tabmargins=[2, 5, 0, 0])
        style.configure('TNotebook.Tab', background=bg_color, foreground=text_color, padding=[10, 2])
        style.map('TNotebook.Tab', 
                 background=[('selected', accent_color), ('active', accent_light)],
                 foreground=[('selected', text_color), ('active', text_color)])
        
        # Configure Treeview
        style.configure('Treeview', 
                      background=input_bg, 
                      foreground=text_color,
                      fieldbackground=input_bg)
        style.map('Treeview', 
                background=[('selected', accent_color)],
                foreground=[('selected', text_color)])
        
        # Configure LabelFrame
        style.configure('TLabelframe', background=bg_color)
        style.configure('TLabelframe.Label', background=bg_color, foreground=text_color)
        
        # Set window background
        root.configure(bg=bg_color)
        
        return {
            'bg': bg_color,
            'fg': text_color,
            'accent': accent_color,
            'accent_light': accent_light,
            'input_bg': input_bg
        }
    
    @staticmethod
    def apply_light_theme(root: tk.Tk) -> Dict[str, str]:
        """
        Apply light theme to tkinter window.
        
        Args:
            root: Root Tkinter window
            
        Returns:
            Dict[str, str]: Dictionary of theme colors
        """
        # Define colors
        bg_color = "#F0F0F0"
        text_color = "#333333"
        accent_color = "#5A32A8"
        accent_light = "#7D59C0"
        input_bg = "#FFFFFF"
        
        style = ttk.Style()
        style.theme_use('clam')  # Use clam theme as base
        
        # Configure common styles
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=text_color)
        style.configure('TButton', background=accent_color, foreground="#FFFFFF")
        style.map('TButton', 
                 background=[('active', accent_light), ('pressed', accent_color)],
                 foreground=[('active', "#FFFFFF"), ('pressed', "#FFFFFF")])
        
        style.configure('TCheckbutton', background=bg_color, foreground=text_color)
        style.map('TCheckbutton', 
                 background=[('active', bg_color)],
                 foreground=[('active', text_color)])
        
        style.configure('TEntry', fieldbackground=input_bg, foreground=text_color)
        style.configure('TNotebook', background=bg_color, tabmargins=[2, 5, 0, 0])
        style.configure('TNotebook.Tab', background=bg_color, foreground=text_color, padding=[10, 2])
        style.map('TNotebook.Tab', 
                 background=[('selected', accent_color), ('active', accent_light)],
                 foreground=[('selected', "#FFFFFF"), ('active', "#FFFFFF")])
        
        # Configure Treeview
        style.configure('Treeview', 
                      background=input_bg, 
                      foreground=text_color,
                      fieldbackground=input_bg)
        style.map('Treeview', 
                background=[('selected', accent_color)],
                foreground=[('selected', "#FFFFFF")])
        
        # Configure LabelFrame
        style.configure('TLabelframe', background=bg_color)
        style.configure('TLabelframe.Label', background=bg_color, foreground=text_color)
        
        # Set window background
        root.configure(bg=bg_color)
        
        return {
            'bg': bg_color,
            'fg': text_color,
            'accent': accent_color,
            'accent_light': accent_light,
            'input_bg': input_bg
        }
    
    @staticmethod
    def create_tooltip(widget: tk.Widget, text: str) -> None:
        """
        Create a tooltip for a widget.
        
        Args:
            widget: Widget to add tooltip to
            text: Tooltip text
        """
        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            # Create tooltip window
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{x}+{y}")
            
            frame = ttk.Frame(tooltip, style='Tooltip.TFrame')
            frame.pack(ipadx=5, ipady=5)
            
            label = ttk.Label(frame, text=text, style='Tooltip.TLabel', wraplength=250)
            label.pack()
            
            widget.tooltip = tooltip
            
        def leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
    
    @staticmethod
    def create_scrollable_frame(parent: tk.Widget) -> Tuple[tk.Canvas, ttk.Frame]:
        """
        Create a scrollable frame.
        
        Args:
            parent: Parent widget
            
        Returns:
            Tuple[tk.Canvas, ttk.Frame]: Canvas and scrollable frame
        """
        # Create a canvas with scrollbar
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        return canvas, scrollable_frame