import tkinter as tk
from tkinter import ttk

class InfoFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure((0, 1), weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text="Model Info & OOP", style="Heading.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )

        self.model_text = tk.Text(self, wrap="word", height=6, state="disabled")
        self.model_text.grid(row=1, column=0, sticky="nsew", padx=(0, 4))

        self.oop_text = tk.Text(self, wrap="word", height=6, state="disabled")
        self.oop_text.grid(row=1, column=1, sticky="nsew", padx=(4, 0))

    def set_info(self, info):
        self._update_text(self.model_text, info if isinstance(info, str) else "\n".join(f"{k}: {v}" for k,v in info.items()))
        oop = (
            "• Encapsulation: hidden pipelines\n"
            "• Polymorphism: same run() call\n"
            "• Overriding: custom run()\n"
            "• Decorators: log_action, timeit\n"
            "• Inheritance: Base + Mixins"
        )
        self._update_text(self.oop_text, oop)

    def _update_text(self, widget, content):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", content)
        widget.config(state="disabled")
