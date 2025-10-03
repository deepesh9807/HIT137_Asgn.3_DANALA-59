# userInterface/output_frame.py
import os, shutil, platform, subprocess
from tkinter import ttk, filedialog
import tkinter as tk
from PIL import Image, ImageTk
import imageio.v3 as iio

from userInterface._parts import ThemedScrolledText

class OutputFrame(ttk.LabelFrame):
    def __init__(self, master):
        super().__init__(master, text="Model Output")
        self.columnconfigure(0, weight=1)
        # Make the text area and preview pane share vertical space
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Text log area at the top
        self.txt = ThemedScrolledText(self, height=8)
        self.txt.grid(row=0, column=0, sticky="nsew", padx=6, pady=(6,3))

        # Preview
        pane = ttk.Frame(self)
        pane.grid(row=1, column=0, sticky="nsew", padx=6, pady=(3,6))
        pane.columnconfigure(0, weight=1)
        pane.rowconfigure(0, weight=1)

        self.preview = tk.Label(pane, bd=0, highlightthickness=0)
        self.preview.grid(row=0, column=0, sticky="nsew")

         # Fallback entry for user prompts
        btns = ttk.Frame(pane)
        btns.grid(row=1, column=0, sticky="w", pady=(6,0))
        self.btn_open = ttk.Button(btns, text="Open", command=self._open, state="disabled")
        self.btn_save = ttk.Button(btns, text="Save As…", command=self._save_as, state="disabled")
        self.btn_open.pack(side="left", padx=(0,6))
        self.btn_save.pack(side="left")

        ## Fallback entry for user prompts
        self._last_image = None
        self._last_path = None

        # Refresh preview on resize
        self.preview.bind("<Configure>", lambda e: self._refresh_preview())

    def show(self, payload):
        """Accepts str for text, or dict with 'result' string and optional 'image_path'/'video_path'."""
       
        # Clear previous
        self.txt.delete("1.0", "end")
        if isinstance(payload, dict):
            self.txt.insert("1.0", str(payload.get("result", "")))
            path = payload.get("image_path") or payload.get("video_path") or payload.get("still_path")
        else:
            self.txt.insert("1.0", str(payload))
            path = None

        self._last_path = path
        self._render_preview(path)

    def clear(self):
        self.txt.delete("1.0", "end")
        self._last_path = None
        self.preview.configure(image="", text="")
        self.btn_open.configure(state="disabled")
        self.btn_save.configure(state="disabled")

    #******** Preview handling ********#
    def _render_preview(self, path):
        if not path or not os.path.exists(path):
            self.preview.configure(image="", text="")
            self.btn_open.configure(state="disabled")
            self.btn_save.configure(state="disabled")
            return

        img = None
        try:
            if path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif")):
                img = Image.open(path).convert("RGB")
            elif path.lower().endswith((".mp4", ".mov", ".webm", ".avi", ".mkv")):
                # load first frame of video
                frame = iio.imread(path, index=0)
                img = Image.fromarray(frame)
        except Exception:
            img = None

        if img is None:
            self.preview.configure(image="", text=os.path.basename(path))
            self.btn_open.configure(state="normal")
            self.btn_save.configure(state="normal")
            return
        # Fallback entry for user prompts
        # Resize image to fit max 720x720 but min 220x220
        try:
            min_dim = 220
            max_dim = 720
            w0, h0 = img.size
            # Compute scale factors added
            scale_down = min(max_dim / w0, max_dim / h0, 1.0)
            scale_up = max(min_dim / w0, min_dim / h0, 1.0)
           
            # final size
            if scale_up > 1.0:
                new_w = int(w0 * scale_up)
                new_h = int(h0 * scale_up)
            else:
                new_w = int(w0 * scale_down)
                new_h = int(h0 * scale_down)

            # Clamp to min/max sizes
            new_w = max(1, min(new_w, max_dim))
            new_h = max(1, min(new_h, max_dim))

            self._raw_img = img.resize((new_w, new_h), resample=Image.LANCZOS)
        except Exception:
            self._raw_img = img

        self._refresh_preview()
        self.btn_open.configure(state="normal")
        self.btn_save.configure(state="normal")

    def _refresh_preview(self):
        if not hasattr(self, "_raw_img"): return
        w = max(self.preview.winfo_width(), 1)
        h = max(self.preview.winfo_height(), 1)
        img = self._raw_img.copy()
        img.thumbnail((w, h))
        self._last_image = ImageTk.PhotoImage(img)
        self.preview.configure(image=self._last_image)

    #******* Open / Save As *******#
    def _open(self):
        if not self._last_path or not os.path.exists(self._last_path): return
        system = platform.system()
        try:
            if system == "Darwin":
                subprocess.Popen(["open", self._last_path])
            elif system == "Windows":
                os.startfile(self._last_path)  # type: ignore
            else:
                subprocess.Popen(["xdg-open", self._last_path])
        except Exception:
            pass

    def _save_as(self):
        if not self._last_path or not os.path.exists(self._last_path): return
        base = os.path.basename(self._last_path)
        ext  = os.path.splitext(base)[1].lower()
        types = [("Image/Video", f"*{ext}"), ("All files", "*.*")]
        dest = filedialog.asksaveasfilename(defaultextension=ext, initialfile=base, filetypes=types)
        if dest:
            shutil.copy2(self._last_path, dest)
