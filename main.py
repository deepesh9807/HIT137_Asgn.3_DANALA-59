import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from itertools import cycle

from helpers.theme import apply_theme
from userInterface.input_frame import InputFrame
from userInterface.output_frame import OutputFrame
from userInterface.info_frame import InfoFrame
from userInterface.preferences import PreferencesDialog

# --- Model Adapters ---
from app_model.text_sentiment import TextSentimentAdapter
from app_model.image_classifier import ImageClassifierAdapter
from app_model.image_to_text import ImageToTextAdapter
from app_model.text_to_image import TextToImageAdapter


class FloatingSpinner(ttk.Frame):
    """Floating spinner for showing busy state."""
    def __init__(self, master, text="Loading..."):
        super().__init__(master, style="Overlay.TFrame")
        self.place(relx=0.5, rely=0.5, anchor="center")
        self.lights = cycle(["◐", "◓", "◑", "◒"])
        self.running = False

        self.label = ttk.Label(self, text=text, font=("Segoe UI", 12))
        self.label.pack(pady=(0, 4))

        self.spinner_label = ttk.Label(self, text="", font=("Segoe UI", 20))
        self.spinner_label.pack()

    def start(self):
        self.running = True
        self._animate()

    def stop(self):
        self.running = False
        self.destroy()

    def _animate(self):
        if not self.running:
            return
        self.spinner_label.config(text=next(self.lights))
        self.after(150, self._animate)


class AIApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Demo App")
        self.geometry("1040x680")
        self.minsize(860, 560)
        apply_theme(self)

        self._is_running = False
        self._thread = None
        self._result = None
        self._error = None
        self._current_model = None
        self.spinner = None

        # Model registry
        self.models = {
            "Text Classification": TextSentimentAdapter(),
            "Image Classification": ImageClassifierAdapter(),
            "Image-to-Text": ImageToTextAdapter(),
            "Text-to-Image": TextToImageAdapter(),
        }
        self.selected_model = tk.StringVar(value="Text Classification")

        # Layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._create_menu()
        self._create_layout()
        self._bind_keys()

    # ---------------- Menu ---------------- #
    def _create_menu(self):
        menu_bar = tk.Menu(self)
        self.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Settings", command=lambda: PreferencesDialog(self), accelerator="Ctrl+,")
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.destroy, accelerator="Ctrl+Q")
        menu_bar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(
            label="About",
            command=lambda: messagebox.showinfo(
                "About",
                "AI Demo App (Tkinter + Hugging Face)\n\n"
                "Models supported:\n"
                "- Text Classification\n"
                "- Image Classification\n"
                "- Image-to-Text\n"
                "- Text-to-Image\n"
            ),
        )
        menu_bar.add_cascade(label="Help", menu=help_menu)

    # ---------------- Layout ---------------- #
    def _create_layout(self):
        # Top controls
        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=8)
        top.columnconfigure(2, weight=1)

        ttk.Label(top, text="Choose Model:").grid(row=0, column=0, sticky="w")
        self.combo = ttk.Combobox(top, textvariable=self.selected_model,
                                  values=list(self.models.keys()), state="readonly", width=26)
        self.combo.grid(row=0, column=1, padx=6, sticky="w")

        ttk.Button(top, text="Load", command=self.load_model, style="Accent.TButton").grid(row=0, column=3, sticky="w")

        # Middle panes
        panes = ttk.Panedwindow(self, orient="horizontal")
        panes.grid(row=1, column=0, sticky="nsew", padx=12, pady=6)

        self.input_panel = InputFrame(panes)
        self.output_panel = OutputFrame(panes)
        panes.add(self.input_panel, weight=1)
        panes.add(self.output_panel, weight=2)

        # Bottom controls
        controls = ttk.Frame(self)
        controls.grid(row=2, column=0, sticky="w", padx=12, pady=6)

        self.run_btn = ttk.Button(controls, text="Run", command=self.run_model)
        self.run_btn.pack(side="left", padx=5)

        ttk.Button(controls, text="Clear", command=self.output_panel.clear).pack(side="left", padx=5)

        # Info + Status
        self.info_panel = InfoFrame(self)
        self.info_panel.grid(row=3, column=0, sticky="ew", padx=12, pady=(6, 12))

        self.status_bar = ttk.Label(self, anchor="w")
        self.status_bar.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 10))

    # ---------------- Key Bindings ---------------- #
    def _bind_keys(self):
        self.bind_all("<Control-r>", lambda e: self.run_model())
        self.bind_all("<Control-l>", lambda e: self.load_model())
        self.bind_all("<Control-q>", lambda e: self.destroy())
        self.bind_all("<Escape>", lambda e: self.cancel_run())
        self.bind_all("<Control-comma>", lambda e: PreferencesDialog(self))

    # ---------------- Busy State ---------------- #
    def _set_busy(self, busy: bool, text=""):
        self._is_running = busy
        state = "disabled" if busy else "normal"
        self.combo.configure(state=state if not busy else "disabled")
        self.run_btn.configure(state=state)
        if busy:
            self.spinner = FloatingSpinner(self, text=text)
            self.spinner.start()
        elif self.spinner:
            self.spinner.stop()
            self.spinner = None
        if text:
            self._set_status(text)

    # ---------------- Model Handling ---------------- #
    def load_model(self):
        if self._is_running:
            return
        model_name = self.selected_model.get()
        if self._current_model and self._current_model != model_name:
            ok = messagebox.askyesno("Confirm", f"Replace '{self._current_model}' with '{model_name}'?")
            if not ok:
                return

        try:
            self._set_busy(True, f"Loading {model_name}...")
            self.update_idletasks()
            self.models[model_name].load()
            self.info_panel.set_info(self.models[model_name].info())
            self._set_status(f"{model_name} loaded")
            messagebox.showinfo("Success", f"{model_name} loaded successfully")
            self._current_model = model_name
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self._set_status("Failed to load model")
        finally:
            self._set_busy(False)

    def run_model(self):
        if self._is_running:
            return
        name = self.selected_model.get()
        adapter = self.models[name]
        if getattr(adapter, "_pipe", None) is None and not hasattr(adapter, "_model"):
            messagebox.showwarning("Warning", f"Load '{name}' before running.")
            return

        payload = self.input_panel.get_payload()
        task_input = payload.get("prompt") if payload.get("mode") == "text" else payload.get("image_path") or payload.get("prompt")

        self._result, self._error = None, None

        def worker():
            try:
                t0 = time.time()
                res = adapter.run(task_input)
                if not isinstance(res, dict):
                    res = {"result": str(res)}
                res.setdefault("_time_ms", (time.time() - t0) * 1000)
                self._result = res
            except Exception as ex:
                self._error = ex

        self._set_busy(True, f"Running {name}...")
        self._thread = threading.Thread(target=worker, daemon=True)
        self._thread.start()
        self.after(100, self._check_thread, name, adapter)

    def _check_thread(self, name, adapter):
        if self._thread and self._thread.is_alive():
            self.after(100, self._check_thread, name, adapter)
            return

        self._set_busy(False)
        if self._error:
            self.output_panel.show({"result": f"Error: {self._error}"})
            self._set_status("Run failed")
            return

        output = self._result or {}
        self.output_panel.show(output)
        try:
            self.info_panel.set_info(adapter.info())
        except Exception:
            pass
        ms = output.get("_time_ms")
        self._set_status(f"Finished {name} in {ms:.1f} ms" if ms else f"Finished {name}")

    def cancel_run(self):
        if self._is_running:
            self._set_busy(False, "Cancelled")
            self._thread = None

    def _set_status(self, msg: str):
        self.status_bar.config(text=msg)


if __name__ == "__main__":
    AIApp().mainloop()
