import threading
import keyboard

from .config_manager import config, load_config, save_config
from .screenshot import capture_selected_region
from .ocr import image_to_text
from .ollama_integration import get_ai_response
from .gui import SystemTrayApp
from .utils import initial_checks, log_info, log_error
from .auto_selector import get_auto_selector

processing_lock = threading.Lock()
app_running = True


def process_screenshot_workflow(tray_app_instance_ref: SystemTrayApp):
    if not processing_lock.acquire(blocking=False):
        log_info("Capture already in progress. Ignoring new request.")
        return

    active_popup = None
    screenshot_region = None
    current_config = load_config()
    popup_enabled = current_config.get('popup_enabled', True)
    log_info("Screenshot workflow started")

    try:
        if popup_enabled:
            active_popup = tray_app_instance_ref._show_response_popup(
                title="QuizSnapper",
                message="Processing your screenshot...",
                start_auto_close=False
            )

            if not active_popup:
                log_error("Failed to create popup window")

        pil_image = capture_selected_region()
        if not pil_image:
            log_info("Screenshot capture cancelled")
            if active_popup:
                active_popup.close()
            return

        text_from_ocr = image_to_text(pil_image)
        ai_response = get_ai_response(text_from_ocr)

        if popup_enabled and active_popup:
            active_popup.update_text(
                ai_response,
                new_title="Answer",
                auto_close_when_final=True
            )
        elif not popup_enabled:
            log_info(f"Popup disabled. Answer: {ai_response}")

        auto_selector = get_auto_selector()
        if auto_selector.is_enabled():
            log_info("Auto-selector is enabled, attempting to select answers")
            auto_selector.find_and_click_answers(ai_response, screenshot_region)

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


def toggle_auto_selector(tray_app_instance_ref: SystemTrayApp):
    auto_selector = get_auto_selector()
    new_state = not auto_selector.is_enabled()
    auto_selector.set_enabled(new_state)
    
    current_config = load_config()
    current_config['auto_select_enabled'] = new_state
    save_config(current_config)
    
    status_text = "ENABLED" if new_state else "DISABLED"
    status_icon = "✓" if new_state else "✗"
    message = f"{status_icon} Auto-Selector {status_text}"
    
    log_info(f"Auto-selector toggled via shortcut: {status_text}")
    
    tray_app_instance_ref._recreate_tray_icon()
    
    popup = tray_app_instance_ref._show_response_popup(
        title="Auto-Selector",
        message=message,
        start_auto_close=False
    )
    if popup:
        tray_app_instance_ref.root.after(2000, popup.close)


def toggle_popup(tray_app_instance_ref: SystemTrayApp):
    current_config = load_config()
    new_state = not current_config.get('popup_enabled', True)
    current_config['popup_enabled'] = new_state
    save_config(current_config)
    
    status_text = "ENABLED" if new_state else "DISABLED"
    status_icon = "✓" if new_state else "✗"
    message = f"{status_icon} Popup Display {status_text}"
    
    log_info(f"Popup display toggled via shortcut: {status_text}")
    
    tray_app_instance_ref._recreate_tray_icon()
    
    popup = tray_app_instance_ref._show_response_popup(
        title="Popup Display",
        message=message,
        start_auto_close=False
    )
    if popup:
        tray_app_instance_ref.root.after(2000, popup.close)


def setup_hotkey(tray_app_instance_ref: SystemTrayApp):
    shortcut = config.get('shortcut', 'ctrl+alt+x')
    toggle_shortcut = config.get('auto_selector_toggle_shortcut', 'ctrl+alt+a')
    popup_toggle_shortcut = config.get('popup_toggle_shortcut', 'ctrl+alt+p')
    
    try:
        keyboard.add_hotkey(shortcut, process_screenshot_workflow, args=(tray_app_instance_ref,))
        log_info(f"Capture hotkey registered: {shortcut}")
        
        keyboard.add_hotkey(toggle_shortcut, toggle_auto_selector, args=(tray_app_instance_ref,))
        log_info(f"Auto-selector toggle hotkey registered: {toggle_shortcut}")
        
        keyboard.add_hotkey(popup_toggle_shortcut, toggle_popup, args=(tray_app_instance_ref,))
        log_info(f"Popup toggle hotkey registered: {popup_toggle_shortcut}")
        
        print(f"QuizSnapper is running.")
        print(f"  Press '{shortcut}' to capture screenshot")
        print(f"  Press '{toggle_shortcut}' to toggle auto-selector")
        print(f"  Press '{popup_toggle_shortcut}' to toggle popup display")
    except Exception as e:
        log_error(f"Failed to register hotkeys: {e}", exc_info=True)
        tray_app_instance_ref._show_generic_error_dialog(
            "Hotkey Error", 
            f"Failed to register hotkeys: {e}\n\nTry different shortcuts in config.json."
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
    log_info("QuizSnapper v1.3.0 starting...")
    
    current_config = load_config()
    save_config(current_config)

    auto_selector = get_auto_selector()
    auto_selector.set_enabled(current_config.get('auto_select_enabled', False))

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