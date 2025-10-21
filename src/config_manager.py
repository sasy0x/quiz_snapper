import json
from pathlib import Path

CONFIG_FILE = Path(__file__).resolve().parent.parent / "config.json"

DEFAULT_CONFIG = {
    "version": "1.2.0",
    "shortcut": "ctrl+alt+x",
    "debug_mode": False,
    "log_file": "app.log",
    "tray_icon": "default",
    "tray_menu_title": "QuizSnapper",
    "ocr_lang": "eng+ita",
    "popup_enabled": True,
    "popup_position": "bottom_right",
    "popup_width": 420,
    "popup_height": 280,
    "popup_auto_close_delay_ms": 7000,
    "popup_transparency": 0.95,
    "auto_select_enabled": False,
    "ai_provider": "ollama",
    "ollama_model": "deepseek-r1:1.5b",
    "ollama_api_url": "http://localhost:11434/api/generate",
    "api_url": "",
    "api_key": "",
    "api_model": "",
    "prompt_template": "You are a quiz assistant. Analyze the question and provide ONLY the correct answer.\n\nFor MULTIPLE CHOICE: Provide ONLY the correct option text (not all options). If multiple answers are required, the question will explicitly state 'select all that apply' or 'choose two' - only then provide multiple answers.\nFor MATCH questions: Show connections as 'A → 1', 'B → 2', etc.\nFor TRUE/FALSE: State True or False\nFor SHORT ANSWER: Provide the direct answer\n\nQuestion: [TEXT]\n\nAnswer:",
    "show_explanation": True,
    "clean_output": True,
    "use_pdf_context": False,
    "knowledge_base_folder": "knowledge_base"
}

def load_config():
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
            return config
    except json.JSONDecodeError:
        print(f"Error decoding {CONFIG_FILE}. Using default configuration.")
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

def save_config(config_data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f, indent=2)

config = load_config()

if __name__ == '__main__':
    print("Current configuration:")
    for key, value in config.items():
        print(f"- {key}: {value}")