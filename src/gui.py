import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageDraw
import pystray
from pathlib import Path
import os
import sys
import subprocess
import threading
import tkinter.messagebox

try:
    from .config_manager import config, save_config, load_config, CONFIG_FILE
    from .utils import log_info, log_error, log_warning
except ImportError:
    print("Warning: Could not import config_manager or utils.")
    class MockConfig:
        def get(self, key, default=None):
            defaults = {
                "popup_width": 400,
                "popup_height": 250,
                "popup_auto_close_delay_ms": 7000,
                "popup_position": "bottom_right",
                "ollama_model": "deepseek-r1:1.5b"
            }
            return defaults.get(key, default)
    config = MockConfig()
    CONFIG_FILE = "config.json"
    def log_info(msg, *args, **kwargs): print(f"INFO: {msg}")
    def log_error(msg, *args, **kwargs): print(f"ERROR: {msg}")
    def log_warning(msg, *args, **kwargs): print(f"WARNING: {msg}")

BASE_DIR = Path(__file__).resolve().parent.parent

class ResponsePopup:
    def __init__(self, parent_tk_root, title="Processing...", initial_text="Please wait...", start_auto_close=False):
        self.parent_tk_root = parent_tk_root
        self.root = None
        self.title_bar_frame = None
        self.title_label_widget = None
        self.text_area = None
        self.after_id_autoclose = None
        self.is_active = False
        self.drag_start_x = None
        self.drag_start_y = None
        self._pending_updates = []

        if not self.parent_tk_root:
            log_error("ResponsePopup initialization failed")
            return

        self.parent_tk_root.after(0, self._create_window, title, initial_text, start_auto_close)

    def _create_window(self, title_str, text_content, start_auto_close):
        if not self.parent_tk_root or not self.parent_tk_root.winfo_exists():
            log_error("Cannot create popup window")
            self.is_active = False
            self.root = None
            return

        try:
            self.root = tk.Toplevel(self.parent_tk_root)
            self.root.attributes("-topmost", True)
            self.root.overrideredirect(True)
            
            transparency = config.get("popup_transparency", 0.95)
            self.root.attributes("-alpha", transparency)

            self.root.deiconify()
            self.root.lift()

            width = config.get("popup_width", 420)
            height = config.get("popup_height", 280)
            bg_color = "#2b2b2b"
            title_bar_bg = "#1e1e1e"
            text_fg = "#e0e0e0"
            border_color = "#404040"

            self.root.configure(bg=border_color)
            self.root.geometry(f"{width}x{height}")

            main_frame = tk.Frame(self.root, bg=bg_color)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

            self.title_bar_frame = tk.Frame(main_frame, bg=title_bar_bg, height=32)
            self.title_bar_frame.pack(fill=tk.X, side=tk.TOP)
            self.title_bar_frame.pack_propagate(False)

            close_button_left = tk.Button(self.title_bar_frame, text="✕", command=self.close,
                                         bg=title_bar_bg, fg="#888888", activebackground="#333333",
                                         activeforeground="#ffffff", relief=tk.FLAT, width=3, 
                                         font=("Segoe UI", 9), bd=0, highlightthickness=0, cursor="hand2")
            close_button_left.pack(side=tk.LEFT, padx=4, pady=4)

            self.title_label_widget = tk.Label(self.title_bar_frame, text=title_str, fg=text_fg, 
                                              bg=title_bar_bg, font=("Segoe UI", 10, "bold"), cursor="fleur")
            self.title_label_widget.pack(side=tk.LEFT, padx=10, pady=2, expand=True, fill=tk.X)

            close_button_right = tk.Button(self.title_bar_frame, text="✕", command=self.close,
                                          bg=title_bar_bg, fg="#888888", activebackground="#333333",
                                          activeforeground="#ffffff", relief=tk.FLAT, width=3, 
                                          font=("Segoe UI", 9), bd=0, highlightthickness=0, cursor="hand2")
            close_button_right.pack(side=tk.RIGHT, padx=4, pady=4)

            for widget in [self.title_bar_frame, self.title_label_widget]:
                widget.bind("<ButtonPress-1>", self._start_move)
                widget.bind("<ButtonRelease-1>", self._stop_move)
                widget.bind("<B1-Motion>", self._do_move)

            self.text_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, bg=bg_color, fg=text_fg,
                                                       font=("Segoe UI", 11), relief=tk.FLAT, bd=0,
                                                       insertbackground=text_fg, state='normal',
                                                       highlightthickness=0, padx=8, pady=8)
            self.text_area.pack(padx=12, pady=(8, 12), expand=True, fill=tk.BOTH)
            self.text_area.insert(tk.END, text_content)
            self.text_area.configure(state='disabled')

            self._position_window()
            self.is_active = True
            
            self.root.update_idletasks()
            self.root.after(50, lambda: self.root.attributes("-alpha", 0.95))

            queued_updates = list(self._pending_updates)
            self._pending_updates.clear()
            for update_args in queued_updates:
                self._do_update_text(*update_args)

            if start_auto_close and self.is_active:
                self._schedule_auto_close()

        except Exception as e:
            log_error(f"ResponsePopup: Error creating window: {e}", exc_info=True)
            if self.root and self.root.winfo_exists():
                try:
                    self.root.destroy()
                except tk.TclError:
                    pass
            self.root = None
            self.is_active = False


    def update_text(self, new_text: str, new_title: str | None = None, auto_close_when_final: bool = False):
        if self.root and self.root.winfo_exists():
            self.root.after(0, self._do_update_text, new_text, new_title, auto_close_when_final)
        else:
            self._pending_updates.append((new_text, new_title, auto_close_when_final))


    def _do_update_text(self, new_text: str, new_title: str | None, auto_close_when_final: bool):
        if not self.root or not self.root.winfo_exists():
            return

        try:
            if new_title is not None and self.title_label_widget:
                self.title_label_widget.config(text=new_title)

            if self.text_area:
                current_state = self.text_area.cget('state')
                self.text_area.configure(state='normal')
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, new_text)
                self.text_area.configure(state=current_state)

            self.root.deiconify()
            self.root.lift()

            if auto_close_when_final:
                self._schedule_auto_close()
            else:
                self._cancel_auto_close()

        except Exception as e:
            log_error(f"ResponsePopup: Error during _do_update_text: {e}", exc_info=True)


    def _start_move(self, event):
        if self.root:
            self.drag_start_x = event.x
            self.drag_start_y = event.y

    def _stop_move(self, event):
        self.drag_start_x = None
        self.drag_start_y = None

    def _do_move(self, event):
        if self.root and self.drag_start_x is not None and self.drag_start_y is not None:
            try:
                x = self.root.winfo_x() + event.x - self.drag_start_x
                y = self.root.winfo_y() + event.y - self.drag_start_y
                self.root.geometry(f"+{x}+{y}")
            except tk.TclError:
                pass
            except Exception as e:
                log_error(f"Error moving window: {e}", exc_info=True)


    def _handle_generic_click(self, event):
        pass

    def _position_window(self):
        """Positions the window based on the configured position."""
        if not self.root:
            return

        position = config.get("popup_position", "bottom_right").lower()
        width = self.root.winfo_width()
        height = self.root.winfo_height()

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        if position == "bottom_right":
            x = screen_width - width - 20
            y = screen_height - height - 60
        elif position == "top_right":
            x = screen_width - width - 20
            y = 20
        elif position == "bottom_left":
            x = 20
            y = screen_height - height - 60
        elif position == "top_left":
            x = 20
            y = 20
        elif position == "center":
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
        else:
            log_warning(f"Unknown popup position: {position}")
            x = screen_width - width - 20
            y = screen_height - height - 60

        x, y = int(x), int(y)
        self.root.geometry(f"+{x}+{y}")

    def _schedule_auto_close(self):
        delay_ms = config.get("popup_auto_close_delay_ms", 7000)
        if delay_ms > 0:
            self._cancel_auto_close()
            self.after_id_autoclose = self.root.after(delay_ms, self.close)


    def _cancel_auto_close(self):
        if self.after_id_autoclose and self.root and self.root.winfo_exists():
            self.root.after_cancel(self.after_id_autoclose)
            self.after_id_autoclose = None


    def close(self):
        if self.parent_tk_root and self.parent_tk_root.winfo_exists():
            self.parent_tk_root.after(0, self._do_close)
        elif self.root and self.root.winfo_exists():
            self.root.after(0, self._do_close)
        else:
            self._do_close_cleanup_state()

    def _do_close(self):
        self._cancel_auto_close()
        if self.root and self.root.winfo_exists():
            try:
                self.root.destroy()
            except tk.TclError as e:
                log_error(f"Error destroying window: {e}", exc_info=True)
        self._do_close_cleanup_state()

    def _do_close_cleanup_state(self):
        self.root = None
        self.is_active = False


class SystemTrayApp:
    def __init__(self, on_exit_callback=None, on_capture_callback=None):
        self.root = tk.Tk()
        self.root.withdraw()

        self.on_exit_callback = on_exit_callback
        self.on_capture_callback = on_capture_callback
        self.icon = self._create_tray_icon()

    def _create_tray_icon(self):
        icon_name = config.get("tray_icon", "default")
        icon_path = BASE_DIR / "assets" / f"{icon_name}.png"
        image = None
        
        try:
            if icon_path.is_file():
                image = Image.open(icon_path)
                log_info(f"Loaded tray icon: {icon_path}")
            else:
                log_warning(f"Icon not found: {icon_path}. Using default.")
        except Exception as e:
            log_error(f"Error loading icon {icon_path}: {e}", exc_info=True)

        if image is None:
            width, height = 64, 64
            image = Image.new('RGB', (width, height), 'black')
            dc = ImageDraw.Draw(image)
            dc.rectangle((width // 4, height // 4, width * 3 // 4, height * 3 // 4), fill='white')

        menu_title = config.get("tray_menu_title", "QuizSnapper")

        menu = (
            pystray.MenuItem('Capture Screenshot', self._capture_screenshot_action),
            pystray.MenuItem('Open Configuration', self._open_config_action),
            pystray.MenuItem('View Logs', self._view_logs_action),
            pystray.MenuItem('Exit', self._exit_action)
        )

        icon = pystray.Icon("quizsnapper", image, menu_title, menu)
        return icon

    def _capture_screenshot_action(self, icon, item):
        if self.on_capture_callback:
            threading.Thread(target=self.on_capture_callback, args=(self,), daemon=True).start()
        else:
            self._show_generic_error_dialog("Action Failed", "Capture callback not configured.")


    def _open_config_action(self, icon, item):
        config_path = Path(CONFIG_FILE).resolve()
        try:
            if sys.platform == "win32":
                os.startfile(config_path)
            elif sys.platform == "darwin":
                subprocess.run(['open', config_path], check=True)
            else:
                subprocess.run(['xdg-open', config_path], check=True)
        except FileNotFoundError:
            log_error(f"Config file not found at {config_path}.")
            self._show_generic_error_dialog("Error", f"Configuration file not found:\n{config_path}")
        except Exception as e:
            log_error(f"Failed to open config file {config_path}: {e}", exc_info=True)
            self._show_generic_error_dialog("Error", f"Failed to open configuration file:\n{e}")


    def _view_logs_action(self, icon, item):
        log_path = Path(config.get("log_file", "app.log")).resolve()
        try:
            if sys.platform == "win32":
                os.startfile(log_path)
            elif sys.platform == "darwin":
                subprocess.run(['open', log_path], check=True)
            else:
                subprocess.run(['xdg-open', log_path], check=True)
        except FileNotFoundError:
            log_error(f"Log file not found at {log_path}.")
            self._show_generic_error_dialog("Error", f"Log file not found:\n{log_path}")
        except Exception as e:
            log_error(f"Failed to open log file {log_path}: {e}", exc_info=True)
            self._show_generic_error_dialog("Error", f"Failed to open log file:\n{e}")


    def _exit_action(self, icon, item):
        self.stop()

    def _show_response_popup(self, title, message, start_auto_close=False):
        try:
            popup = ResponsePopup(self.root, title, message, start_auto_close)
            return popup
        except Exception as e:
            log_error(f"Failed to create popup: {e}", exc_info=True)
            self._show_generic_error_dialog("Popup Error", f"Failed to create response window:\n{e}")
            return None


    def _show_generic_error_dialog(self, title, message):
        self.root.after(0, tkinter.messagebox.showerror, title, message)


    def run(self):
        threading.Thread(target=self.icon.run, daemon=True).start()
        self.root.mainloop()


    def stop(self):
        if self.on_exit_callback:
            self.on_exit_callback()
        if self.icon:
            self.icon.stop()
        if self.root and self.root.winfo_exists():
            self.root.quit()
            self.root.destroy()