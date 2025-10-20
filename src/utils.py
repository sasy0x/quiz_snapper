import subprocess
import logging
import requests
import json
from .config_manager import config
from pytesseract import TesseractNotFoundError

log_file_path = config.get("log_file", "app.log")
logging.basicConfig(
    filename=log_file_path,
    level=logging.DEBUG if config.get("debug_mode") else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'

def debug_print(label: str, data: any):
    if not config.get("debug_mode"):
        return
    
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.MAGENTA}{Colors.BOLD}[DEBUG] {label}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
    
    if isinstance(data, dict):
        for key, value in data.items():
            print(f"{Colors.YELLOW}{key}:{Colors.RESET} {value}")
    elif isinstance(data, (list, tuple)):
        for idx, item in enumerate(data):
            print(f"{Colors.YELLOW}[{idx}]:{Colors.RESET} {item}")
    else:
        print(f"{Colors.WHITE}{data}{Colors.RESET}")
    
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")

def log_info(message):
    logging.info(message)
    if config.get("debug_mode"):
        print(f"{Colors.GREEN}[INFO]{Colors.RESET} {message}")

def log_error(message, exc_info=False):
    logging.error(message, exc_info=exc_info)
    print(f"{Colors.RED}{Colors.BOLD}[ERROR]{Colors.RESET} {message}")

def log_warning(message):
    logging.warning(message)
    print(f"{Colors.YELLOW}[WARNING]{Colors.RESET} {message}")

def is_tesseract_installed():
    try:
        subprocess.run(['tesseract', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError, TesseractNotFoundError):
        return False
    except Exception as e:
        log_error(f"Unexpected error checking Tesseract: {e}")
        return False

def check_ollama_service():
    try:
        ollama_url = config.get('ollama_api_url', 'http://localhost:11434')
        check_url = ollama_url.replace("/api/generate", "/api/tags") if "/api/generate" in ollama_url else ollama_url + "/api/tags"
        response = requests.get(check_url, timeout=3)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False
    except Exception as e:
        log_error(f"Error checking Ollama service: {e}")
        return False

def check_ollama_model_available():
    if not check_ollama_service():
        return False
    try:
        ollama_url = config.get('ollama_api_url', 'http://localhost:11434')
        model_name = config.get('ollama_model', 'deepseek-r1:1.5b')
        check_url = ollama_url.replace("/api/generate", "/api/tags") if "/api/generate" in ollama_url else ollama_url + "/api/tags"

        response = requests.get(check_url, timeout=3)
        if response.status_code == 200:
            models_data = response.json()
            for model_info in models_data.get("models", []):
                if model_info["name"].startswith(model_name):
                    return True
            log_warning(f"Model {model_name} not found in Ollama. Available models: {[m['name'] for m in models_data.get('models', [])]}")
            return False
        log_error(f"Failed to get Ollama models list. Status code: {response.status_code}")
        return False
    except Exception as e:
        log_error(f"Error checking Ollama model availability: {e}")
        return False


def initial_checks(gui_manager_instance=None):
    all_ok = True
    from .config_manager import config, load_config
    load_config()
    if not is_tesseract_installed():
        log_error("Tesseract OCR is not installed or not found in PATH.")
        if gui_manager_instance and hasattr(gui_manager_instance, '_show_tesseract_error_message'):
            gui_manager_instance._show_tesseract_error_message()
        else:
            print("CRITICAL: Tesseract OCR is not installed or not found in PATH.")
        all_ok = False
    else:
        log_info("Tesseract OCR found.")

    ai_provider = config.get('ai_provider', 'ollama')
    log_info(f"Configured AI provider: {ai_provider}")

    if ai_provider == 'ollama':
        if not check_ollama_service():
            log_error(f"Ollama service not responding at {config.get('ollama_api_url', 'http://localhost:11434')}.")
            if gui_manager_instance and hasattr(gui_manager_instance, '_show_ollama_setup_instructions'):
                gui_manager_instance._show_ollama_setup_instructions("Ollama service not responding.")
            else:
                print(f"CRITICAL: Ollama service not responding. Please ensure Ollama is running.")
            all_ok = False
        else:
            log_info("Ollama service is responding.")
            if not check_ollama_model_available():
                model_name = config.get('ollama_model', 'deepseek-r1:1.5b')
                log_error(f"Ollama model '{model_name}' not available.")
                if gui_manager_instance and hasattr(gui_manager_instance, '_show_ollama_setup_instructions'):
                    gui_manager_instance._show_ollama_setup_instructions(f"Ollama model '{model_name}' not found.")
                else:
                    print(f"CRITICAL: Ollama model '{model_name}' not available. Run 'ollama run {model_name}'.")
                all_ok = False
            else:
                log_info(f"Ollama model '{config.get('ollama_model')}' is available.")
    elif ai_provider == 'api':
        api_url = config.get('api_url')
        api_key = config.get('api_key')
        api_model = config.get('api_model')
        if not all([api_url, api_key, api_model]) or \
           api_url == "YOUR_API_ENDPOINT_HERE" or \
           api_key == "YOUR_API_KEY_HERE" or \
           api_model == "YOUR_API_MODEL_NAME_HERE":
            log_error("AI Provider is 'api', but API URL, Key, or Model is not configured or uses placeholders.")
            if gui_manager_instance and hasattr(gui_manager_instance, '_show_generic_error_dialog'):
                 gui_manager_instance._show_generic_error_dialog("API Configuration Error", "API provider is selected, but API URL, Key, or Model is missing or uses placeholder values in config.json. Please configure them.")
            else:
                print("CRITICAL: API provider is 'api', but API URL, Key, or Model is not configured or uses placeholders.")
            all_ok = False
        else:
            log_info(f"API provider configured. Will use model '{api_model}' at '{api_url}'.")
    else:
        log_error(f"Unknown AI provider '{ai_provider}' in configuration.")
        all_ok = False
            
    return all_ok

if __name__ == '__main__':
    from .config_manager import load_config, config
    load_config()

    print("Running utility checks...")
    print("Tesseract:", "OK" if is_tesseract_installed() else "FAILED")
    print("Ollama service:", "OK" if check_ollama_service() else "FAILED")
    if check_ollama_service():
        print(f"Ollama model:", "OK" if check_ollama_model_available() else "FAILED")
    print("\nInitial checks:", "PASSED" if initial_checks() else "FAILED")