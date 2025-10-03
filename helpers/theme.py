import tkinter as tk
from tkinter import ttk
from helpers.config import load_config

# Predefined color schemes
THEME_PRESETS = {
    "Light": {
        "bg": "#ffffff", "fg": "#111111", "accent": "#2563eb",
        "frame_bg": "#f3f4f6", "textbox_bg": "#ffffff", "textbox_fg": "#111111",
        "status_bg": "#f3f4f6", "status_fg": "#111111", "font_size": 10
    },
    "Dark": {
        "bg": "#0f172a", "fg": "#e5e7eb", "accent": "#22d3ee",
        "frame_bg": "#111827", "textbox_bg": "#0b1220", "textbox_fg": "#e5e7eb",
        "status_bg": "#0b1220", "status_fg": "#e5e7eb", "font_size": 10
    },
    "Blue": {
        "bg": "#0b1020", "fg": "#dbeafe", "accent": "#60a5fa",
        "frame_bg": "#0f172a", "textbox_bg": "#0c1428", "textbox_fg": "#dbeafe",
        "status_bg": "#0c1428", "status_fg": "#dbeafe", "font_size": 10
    }
}

def _get_palette(cfg):
    if cfg.get("theme") == "Custom":
        return cfg["custom"]
    return THEME_PRESETS.get(cfg.get("theme"), THEME_PRESETS["Light"])

def _apply_colors_recursive(widget, palette):
    """Apply colors to widget and all children."""
    try:
        if isinstance(widget, (tk.Text, tk.Entry, tk.Listbox, tk.Spinbox)):
            widget.config(
                bg=palette["textbox_bg"], fg=palette["textbox_fg"], insertbackground=palette["textbox_fg"],
                highlightthickness=0, bd=0
            )
        elif isinstance(widget, (tk.Label, tk.Button, tk.Radiobutton, tk.Checkbutton)):
            widget.config(bg=palette["bg"], fg=palette["fg"])
        elif isinstance(widget, (tk.Frame, tk.Toplevel)):
            widget.config(bg=palette["bg"])
    except tk.TclError:
        pass

    for child in widget.winfo_children():
        _apply_colors_recursive(child, palette)

def apply_theme(root: tk.Tk):
    """Apply selected theme to root window and all widgets."""
    cfg = load_config()
    palette = _get_palette(cfg)
    style = ttk.Style(root)

    # Root window
    root.config(bg=palette["bg"])
    try: style.theme_use("clam")
    except tk.TclError: pass

    # Global options
    root.option_add("*Font", ("Segoe UI", palette["font_size"]))
    root.option_add("*Text.background", palette["textbox_bg"])
    root.option_add("*Text.foreground", palette["textbox_fg"])
    root.option_add("*Entry.background", palette["textbox_bg"])
    root.option_add("*Entry.foreground", palette["textbox_fg"])
    root.option_add("*Label.background", palette["bg"])
    root.option_add("*Label.foreground", palette["fg"])
    root.option_add("*Menu.background", palette["bg"])
    root.option_add("*Menu.foreground", palette["fg"])
    root.option_add("*Menu.activeBackground", palette["frame_bg"])
    root.option_add("*Menu.activeForeground", palette["fg"])

    # ttk style mapping
    style.configure("TFrame", background=palette["bg"])
    style.configure("TLabelframe", background=palette["bg"], bordercolor=palette["frame_bg"])
    style.configure("TLabelframe.Label", background=palette["bg"], foreground=palette["fg"])
    style.configure("TLabel", background=palette["bg"], foreground=palette["fg"])
    style.configure("TRadiobutton", background=palette["bg"], foreground=palette["fg"])
    style.map("TRadiobutton", background=[("active", palette["bg"])])
    style.configure("TButton", background=palette["frame_bg"], foreground=palette["fg"])
    style.map("TButton", background=[("active", palette["frame_bg"])])
    style.configure("Accent.TButton", background=palette["accent"], foreground="white")
    style.map("Accent.TButton", background=[("active", palette["accent"])])
    style.configure("TEntry", fieldbackground=palette["textbox_bg"], foreground=palette["textbox_fg"])
    style.configure("TCombobox", fieldbackground=palette["textbox_bg"], background=palette["bg"], foreground=palette["textbox_fg"])
    style.map("TCombobox", fieldbackground=[("readonly", palette["textbox_bg"])])

    style.configure("Vertical.TScrollbar", background=palette["frame_bg"], troughcolor=palette["frame_bg"])
    style.configure("Horizontal.TProgressbar", background=palette["accent"])

    # Apply recursively
    _apply_colors_recursive(root, palette)
    root._theme_palette = palette
