import threading
import keyboard

from .config_manager import config, load_config, save_config
from .screenshot import capture_selected_region
from .ocr import image_to_text
from .ollama_integration import get_ai_response
from .gui import SystemTrayApp
from .utils import initial_checks, log_info, log_error

processing_lock = threading.Lock()
app_running = True


def process_screenshot_workflow(tray_app_instance_ref: SystemTrayApp):
    if not processing_lock.acquire(blocking=False):
        log_info("Capture already in progress. Ignoring new request.")
        return

    active_popup = None
    log_info("Screenshot workflow started")

    try:
        active_popup = tray_app_instance_ref._show_response_popup(
            title="QuizSnapper",
            message="Processing your screenshot...",
            start_auto_close=False
        )

        if not active_popup:
            log_error("Failed to create popup window")
            return

        pil_image = capture_selected_region()
        if not pil_image:
            log_info("Screenshot capture cancelled")
            if active_popup:
                active_popup.close()
            return

        text_from_ocr = image_to_text(pil_image)
        ai_response = get_ai_response(text_from_ocr)

        if active_popup:
            active_popup.update_text(
                ai_response,
                new_title="Answer",
                auto_close_when_final=True
            )

    except Exception as e:
        log_error(f"Workflow error: {e}", exc_info=True)
        if active_popup:
            active_popup.update_text(
                f"Error: {str(e)}",
                new_title="Error",
                auto_close_when_final=True
            )
    finally:
        if processing_lock.locked():
            processing_lock.release()
            log_info("Screenshot workflow completed")


def setup_hotkey(tray_app_instance_ref: SystemTrayApp):
    shortcut = config.get('shortcut', 'ctrl+alt+x')
    try:
        keyboard.add_hotkey(shortcut, process_screenshot_workflow, args=(tray_app_instance_ref,))
        log_info(f"Hotkey registered: {shortcut}")
        print(f"QuizSnapper is running. Press '{shortcut}' to capture or use the tray icon.")
    except Exception as e:
        log_error(f"Failed to register hotkey '{shortcut}': {e}", exc_info=True)
        tray_app_instance_ref._show_generic_error_dialog(
            "Hotkey Error", 
            f"Failed to register hotkey '{shortcut}': {e}\n\nTry a different shortcut in config.json."
        )
        return False
    return True


def on_app_exit():
    global app_running
    log_info("Application exit requested")
    app_running = False
    if keyboard:
        keyboard.remove_all_hotkeys()
    log_info("Hotkeys unregistered")


def main():
    log_info("QuizSnapper starting...")
    
    current_config = load_config()
    save_config(current_config)

    tray_app = SystemTrayApp(
        on_exit_callback=on_app_exit, 
        on_capture_callback=process_screenshot_workflow
    )
    
    if not initial_checks(gui_manager_instance=tray_app):
        log_error("Initial checks failed. Some features may not work.")

    if not setup_hotkey(tray_app):
        log_error("Hotkey setup failed")

    log_info("Starting system tray...")
    tray_app.run()

    log_info("Application exited")


if __name__ == "__main__":
    main()