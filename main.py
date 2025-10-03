# main.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

from helpers.theme import apply_theme
from userInterface.input_frame import InputFrame
from userInterface.output_frame import OutputFrame
from userInterface.info_frame import InfoFrame
from userInterface.preferences import PreferencesDialog  # preferences.py

# --- Adapters ---
from app_model.text_sentiment import TextSentimentAdapter
from app_model.image_classifier import ImageClassifierAdapter
from app_model.image_to_text import ImageToTextAdapter
from app_model.text_to_image import TextToImageAdapter
from app_model.text_to_video import TextToVideoAdapter  # text_to_video.py


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HIT137 • Tkinter AI GuserInterface")
        self.geometry("1040x680")
        self.minsize(860, 560)
        apply_theme(self)

        # State variables
        self._busy = False
        self._run_thread = None
        self._run_result = None
        self._run_error = None

        # Available model adapters
        self.adapters = {
            "Text Classification": TextSentimentAdapter(),
            "Image Classification": ImageClassifierAdapter(),
            "Image-to-Text": ImageToTextAdapter(),
            "Text-to-Image": TextToImageAdapter(),
            "Text-to-Video": TextToVideoAdapter(),
        }
        self.var_model = tk.StringVar(value="Text Classification")

        # Layout 
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1) 

        self._loaded_model_name = None
        self._buserInterfaceld_menu() 
        self._buserInterfaceld_layout()
        self._bind_shortcuts()

     # Menu
    def _build_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        filem = tk.Menu(menubar, tearoff=0)
        filem.add_command(label="Preferences…", command=lambda: PreferencesDialog(self), accelerator="Ctrl+,")
        filem.add_separator()
        filem.add_command(label="Exit", command=self.destroy, accelerator="Ctrl+Q")
        menubar.add_cascade(label="File", menu=filem)

        helpm = tk.Menu(menubar, tearoff=0)
        helpm.add_command(
            label="About",
            command=lambda: messagebox.showinfo(
                "About",
                "Tkinter + Hugging Face Demo\n\n"
                "app_model available:\n"
                "• Text Classification\n"
                "• Image Classification\n"
                "• Image-to-Text\n"
                "• Text-to-Image\n"
                "• Text-to-Video",
            ),
        )
        menubar.add_cascade(label="Help", menu=helpm)

    # Layout
    def _build_layout(self):
        # Top row: model selection + load button + progress bar at right
        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        top.columnconfigure(2, weight=1)  # spacer

        ttk.Label(top, text="Model:").grid(row=0, column=0, sticky="w")
        self.combo = ttk.Combobox(
            top, textvariable=self.var_model,
            values=list(self.adapters.keys()), width=28, state="readonly"
        )
        self.combo.grid(row=0, column=1, sticky="w", padx=8)

        ttk.Button(top, text="Load Model", style="Accent.TButton",
                   command=self.load_selected).grid(row=0, column=3, sticky="w")

        # Busy indicator
        self.progress = ttk.Progressbar(top, mode="indeterminate", length=220)
        self.progress.grid(row=0, column=4, sticky="e")
        self.progress.stop()

        # Main pane: Add input on left, output on right side
        mid = ttk.Panedwindow(self, orient="horizontal")
        mid.grid(row=1, column=0, sticky="nsew", padx=12, pady=6)

        self.input_frame = InputFrame(mid)
        self.output_frame = OutputFrame(mid)
        mid.add(self.input_frame, weight=1)
        mid.add(self.output_frame, weight=2)

        # Bottom row: Added run button + info + status
        btns = ttk.Frame(self)
        btns.grid(row=2, column=0, sticky="w", padx=12, pady=6)
        self.btn_run = ttk.Button(btns, text="Run Selected Model", command=self.run_selected)
        self.btn_run.pack(side="left", padx=5)
        ttk.Button(btns, text="Clear", command=lambda: self.output_frame.clear()).pack(side="left", padx=5)

        # Info panel
        self.info = InfoFrame(self)
        self.info.grid(row=3, column=0, sticky="ew", padx=12, pady=(6, 12))

        self.status = ttk.Label(self, anchor="w")
        self.status.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 10))


    def _bind_shortcuts(self):
        self.bind_all("<Control-r>", lambda e: self.run_selected())
        self.bind_all("<Control-l>", lambda e: self.load_selected())
        self.bind_all("<Control-q>", lambda e: self.destroy())
        self.bind_all("<Escape>",    lambda e: self._cancel_run())
        self.bind_all("<Control-comma>", lambda e: PreferencesDialog(self))

    #********** Busy state **********#
    def _set_busy(self, flag: bool, status_text: str = ""):
        self._busy = flag
        if flag:
            self.progress.start(12)  # faster
            self.combo.configure(state="disabled")
            self.btn_run.configure(state="disabled")
        else:
            self.progress.stop()
            self.combo.configure(state="readonly")
            self.btn_run.configure(state="normal")
        if status_text:
            self._status(status_text)

    #********** Model loading & running **********#
    def load_selected(self):
        if self._busy:
            return
        name = self.var_model.get()
        # Clear previous output
        try:
            self.output_frame.clear()
        except Exception:
            pass

        # Confirm model switch if needed
        if self._loaded_model_name and self._loaded_model_name != name:
            confirmed = messagebox.askyesno(
                "Switch model?",
                f"A different model ('{self._loaded_model_name}') is already loaded.\n"
                "Loading a new model will clear current inputs and outputs. Continue?",
            )
            if not confirmed:
                return

            # Unload previous model internals if it's possible
            try:
                # Clear input/output
                self.output_frame.clear()
                self.input_frame.clear()

                # Unload previous adapter internals if it's possible
                prev = self.adapters.get(self._loaded_model_name)
                if prev is not None:
                    if hasattr(prev, "_pipe"):
                        try: prev._pipe = None
                        except Exception: pass
                    if hasattr(prev, "_model"):
                        try: prev._model = None
                        except Exception: pass
            except Exception:
                pass

        try:
            self._set_busy(True, f"Loading {name} …")
            self.update_idletasks()
            self.adapters[name].load()
            self.info.set_info(self.adapters[name].info())  # show model info
            self._status(f"Loaded {name}")
            messagebox.showinfo("Loaded", f"{name} loaded successfully.")
            self._loaded_model_name = name
        except Exception as e:
            messagebox.showerror("Load error", str(e))
            self._status("Load error")
        finally:
            self._set_busy(False)

    def run_selected(self):
        if self._busy:
            return
        name = self.var_model.get()
        adapter = self.adapters[name]

        # Check if loaded
        if getattr(adapter, "_pipe", None) is None and not hasattr(adapter, "_model"):
            messagebox.showwarning("Not loaded", f"Please load '{name}' first.")
            return

        payload = self.input_frame.get_payload()
        # Normalize InputFrame data to dict
        # Ensure prompt or path is a string
        # If mode is "image", prefer image_path over prompt
        if isinstance(payload, dict):
            mode = payload.get("mode")
            if mode == "text":
                norm_payload = payload.get("prompt", "")
            elif mode == "image":
                # prefer explicit image_path, fallback to prompt
                norm_payload = payload.get("image_path") or payload.get("prompt", "")
            else:
                # unknown mode, fallback to prompt
                norm_payload = payload.get("prompt", "")
        else:
            norm_payload = payload
        self._run_result = None
        self._run_error = None

        # Run in background thread to avoid blocking the UserInterface
        def _worker():
            try:
                t0 = time.time()
                result = adapter.run(norm_payload)
                if not isinstance(result, dict):
                    result = {"result": str(result)}
                result.setdefault("_ms", (time.time() - t0) * 1000)
                self._run_result = result
            except Exception as ex:
                self._run_error = ex

        self._set_busy(True, f"Running {name} …")
        self._run_thread = threading.Thread(target=_worker, daemon=True)
        self._run_thread.start()
        self.after(80, self._poll_worker, name, adapter)

    def _poll_worker(self, name, adapter):
        if self._run_thread is not None and self._run_thread.is_alive():
            self.after(80, self._poll_worker, name, adapter)
            return

        self._set_busy(False)
        if self._run_error:
            self.output_frame.show({"result": f"Error: {self._run_error}"})
            self._status("Error")
            return

        out = self._run_result or {}
        #  Display output
        self.output_frame.show(out)

        # Update info panel if possible
        try:
            self.info.set_info(adapter.info())
        except Exception:
            pass
        ms = out.get("_ms")
        self._status(f"Ran {name} in {ms:.1f} ms" if ms else f"Ran {name}")

    def _cancel_run(self):
        # Soft cancel: just stop waiting for the thread
        if self._busy:
            self._set_busy(False, "Cancelled (soft)")
            self._run_thread = None

    #******** Status bar ********#
    def _status(self, text: str):
        self.status.config(text=text)


if __name__ == "__main__":
    App().mainloop() 
