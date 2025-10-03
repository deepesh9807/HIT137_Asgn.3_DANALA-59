# preferences.py
import tkinter as tk
from tkinter import ttk, colorchooser
from helpers.config import load_config, save_config
from helpers.theme import apply_theme

class PreferencesDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Preferences")
        self.transient(master)
        self.grab_set()
        self.resizable(False, False)

        apply_theme(self)
        self.cfg = load_config()

        # Layout
        root = ttk.Frame(self, padding=12)
        root.grid(sticky="nsew")
        root.columnconfigure(1, weight=1)

        ttk.Label(root, text="Theme:").grid(row=0, column=0, sticky="w")
        self.var_theme = tk.StringVar(value=self.cfg["theme"])
        combo = ttk.Combobox(
            root, textvariable=self.var_theme,
            values=["Light", "Dark", "Blue", "Custom"],
            state="readonly", width=16
        )
        combo.grid(row=0, column=1, sticky="w", padx=6)
        combo.bind("<<ComboboxSelected>>", self._on_theme_change)

        self.custom_frame = ttk.LabelFrame(root, text="Custom Theme")
        self.custom_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self._build_custom_controls(self.custom_frame)

        # Buttons
        btns = ttk.Frame(root)
        btns.grid(row=2, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="right", padx=6)
        ttk.Button(btns, text="Apply", style="Accent.TButton", command=self._apply).pack(side="right", padx=6)

        self._toggle_custom(self.var_theme.get() == "Custom")

    def _build_custom_controls(self, parent):
        self.vars = {}

        def add_row(label, key, r, col=0):
            ttk.Label(parent, text=label).grid(row=r, column=col, sticky="w", pady=2)
            var = tk.StringVar(value=self.cfg["custom"][key])
            ttk.Entry(parent, textvariable=var, width=14).grid(row=r, column=col+1, sticky="w", padx=6)
            ttk.Button(parent, text="Pick…", command=lambda v=var: self._pick_color(v)).grid(row=r, column=col+2, sticky="w", padx=4)
            self.vars[key] = var

        # Colors
        keys = [
            ("Background", "bg"), ("Foreground", "fg"), ("Accent", "accent"),
            ("Frame background", "frame_bg"), ("Textbox bg", "textbox_bg"),
            ("Textbox fg", "textbox_fg"), ("Status bg", "status_bg"),
            ("Status fg", "status_fg")
        ]
        for i, (label, key) in enumerate(keys):
            add_row(label, key, i % 6, col=0 if i < 6 else 3)

        # Font size
        ttk.Label(parent, text="Base font size").grid(row=2, column=3, sticky="w")
        self.var_font = tk.IntVar(value=int(self.cfg["custom"]["font_size"]))
        ttk.Spinbox(parent, from_=8, to=20, textvariable=self.var_font, width=6).grid(row=2, column=4, sticky="w", padx=6)

    def _on_theme_change(self, _):
        self._toggle_custom(self.var_theme.get() == "Custom")
        apply_theme(self)  # preview

    def _toggle_custom(self, show):
        state = "normal" if show else "disabled"
        for child in self.custom_frame.winfo_children():
            child.configure(state=state)

    def _pick_color(self, var):
        color = colorchooser.askcolor(initialcolor=var.get(), parent=self)[1]
        if color:
            var.set(color)

    def _apply(self):
        cfg = load_config()
        cfg["theme"] = self.var_theme.get()
        if cfg["theme"] == "Custom":
            cfg["custom"].update({k: v.get() for k, v in self.vars.items()})
            cfg["custom"]["font_size"] = int(self.var_font.get())
        save_config(cfg)

        apply_theme(self.master)
        self.destroy()
