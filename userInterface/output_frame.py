import os, shutil, platform, subprocess
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import imageio.v3 as iio

from userInterface._parts import ThemedScrolledText

class OutputFrame(ttk.LabelFrame):
    """Widget to display model output text and preview of images/videos."""

    def __init__(self, master):
        super().__init__(master, text="Model Output")

        # Layout: two rows, one for text log, one for preview
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Top: text log
        self.txt = ThemedScrolledText(self, height=8)
        self.txt.grid(row=0, column=0, sticky="nsew", padx=6, pady=(6, 3))

        # Bottom: preview area + buttons
        pane = ttk.Frame(self)
        pane.grid(row=1, column=0, sticky="nsew", padx=6, pady=(3, 6))
        pane.columnconfigure(0, weight=1)
        pane.rowconfigure(0, weight=1)

        # Preview area (for image/video still)
        self.preview = tk.Label(pane, bd=0, highlightthickness=0)
        self.preview.grid(row=0, column=0, sticky="nsew")

        # Action buttons (open in system viewer, save as…)
        btns = ttk.Frame(pane)
        btns.grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.btn_open = ttk.Button(btns, text="Open", command=self._open, state="disabled")
        self.btn_save = ttk.Button(btns, text="Save As…", command=self._save_as, state="disabled")
        self.btn_open.pack(side="left", padx=(0, 6))
        self.btn_save.pack(side="left")

        # Internal state
        self._last_path = None
        self._last_image = None

        # Refresh preview automatically when widget resizes
        self.preview.bind("<Configure>", lambda e: self._refresh_preview())

    # Show results in text + preview area
    def show(self, payload):
        """Accepts a string, or dict with 'result' plus optional 'image_path'/'video_path'."""
        self.txt.delete("1.0", "end")

        if isinstance(payload, dict):
            self.txt.insert("1.0", str(payload.get("result", "")))
            path = payload.get("image_path") or payload.get("video_path") or payload.get("still_path")
        else:
            self.txt.insert("1.0", str(payload))
            path = None

        self._last_path = path
        self._render_preview(path)

    # Clear all output
    def clear(self):
        self.txt.delete("1.0", "end")
        self.preview.configure(image="", text="")
        self.btn_open.configure(state="disabled")
        self.btn_save.configure(state="disabled")
        self._last_path = None
        self._last_image = None

    # Render an image or video still if a path is available
    def _render_preview(self, path):
        if not path or not os.path.exists(path):
            self.preview.configure(image="", text="")
            self.btn_open.configure(state="disabled")
            self.btn_save.configure(state="disabled")
            return

        img = None
        try:
            # Handle image files
            if path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif")):
                img = Image.open(path).convert("RGB")
            # Handle video files (show first frame)
            elif path.lower().endswith((".mp4", ".mov", ".webm", ".avi", ".mkv")):
                frame = iio.imread(path, index=0)
                img = Image.fromarray(frame)
        except Exception:
            img = None

        # If not an image or failed to load, just show filename
        if img is None:
            self.preview.configure(image="", text=os.path.basename(path))
            self.btn_open.configure(state="normal")
            self.btn_save.configure(state="normal")
            return

        # Resize to stay within 220–720 px
        try:
            min_dim, max_dim = 220, 720
            w, h = img.size

            scale_down = min(max_dim / w, max_dim / h, 1.0)
            scale_up = max(min_dim / w, min_dim / h, 1.0)

            if scale_up > 1.0:
                new_w, new_h = int(w * scale_up), int(h * scale_up)
            else:
                new_w, new_h = int(w * scale_down), int(h * scale_down)

            new_w = max(1, min(new_w, max_dim))
            new_h = max(1, min(new_h, max_dim))

            self._raw_img = img.resize((new_w, new_h), resample=Image.LANCZOS)
        except Exception:
            self._raw_img = img

        self._refresh_preview()
        self.btn_open.configure(state="normal")
        self.btn_save.configure(state="normal")

    # Update preview when window is resized
    def _refresh_preview(self):
        if not hasattr(self, "_raw_img"): 
            return
        w = max(self.preview.winfo_width(), 1)
        h = max(self.preview.winfo_height(), 1)
        img = self._raw_img.copy()
        img.thumbnail((w, h))
        self._last_image = ImageTk.PhotoImage(img)
        self.preview.configure(image=self._last_image)

    # Open file in system viewer
    def _open(self):
        if not self._last_path or not os.path.exists(self._last_path): 
            return
        system = platform.system()
        try:
            if system == "Darwin":  # macOS
                subprocess.Popen(["open", self._last_path])
            elif system == "Windows":
                os.startfile(self._last_path)  # type: ignore
            else:  # Linux/Unix
                subprocess.Popen(["xdg-open", self._last_path])
        except Exception:
            pass

    # Save a copy of the file to a chosen location
    def _save_as(self):
        if not self._last_path or not os.path.exists(self._last_path): 
            return
        base = os.path.basename(self._last_path)
        ext = os.path.splitext(base)[1].lower()
        types = [("Image/Video", f"*{ext}"), ("All files", "*.*")]
        dest = filedialog.asksaveasfilename(defaultextension=ext, initialfile=base, filetypes=types)
        if dest:
            shutil.copy2(self._last_path, dest)
