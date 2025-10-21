import requests
import json
import re
import time
from pathlib import Path
from .config_manager import config
from .utils import log_info, log_error, log_warning


def load_pdf_context() -> str:
    knowledge_base_dir = Path(config.get('knowledge_base_folder', 'knowledge_base'))
    
    if not knowledge_base_dir.exists():
        log_info(f"Knowledge base folder not found: {knowledge_base_dir}")
        return ""
    
    pdf_files = list(knowledge_base_dir.glob('*.pdf'))
    if not pdf_files:
        log_info("No PDF files found in knowledge base folder")
        return ""
    
    try:
        import PyPDF2
        context_parts = []
        
        for pdf_file in pdf_files:
            try:
                with open(pdf_file, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text_parts = []
                    for page in reader.pages:
                        text_parts.append(page.extract_text())
                    
                    if text_parts:
                        context_parts.append(f"Source: {pdf_file.name}\n{''.join(text_parts)}")
                        log_info(f"Loaded PDF: {pdf_file.name}")
            except Exception as e:
                log_warning(f"Failed to read PDF {pdf_file.name}: {e}")
        
        return "\n\n---\n\n".join(context_parts) if context_parts else ""
    
    except ImportError:
        log_warning("PyPDF2 not installed. PDF context loading disabled.")
        return ""


def clean_ai_output(raw_response: str) -> str:
    if not raw_response or raw_response.startswith("Error:"):
        return raw_response
    
    from .config_manager import load_config
    current_config = load_config()
    show_explanation = current_config.get('show_explanation', True)
    clean_output = current_config.get('clean_output', True)
    
    if not clean_output:
        return raw_response
    
    lines = raw_response.split('\n')
    cleaned_lines = []
    in_explanation = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        line = re.sub(r'^(The correct answer is:|The correct answers are:|The correct option is:|The correct options are:|Answer:|Answers?:)\s*', '', line, flags=re.IGNORECASE)
        line = re.sub(r'^\*\*(.+?)\*\*$', r'\1', line)
        line = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
        line = re.sub(r'^\(e\)\s*', '', line, flags=re.IGNORECASE)
        line = re.sub(r'^[_©Oo•\-\*\s]+', '', line)
        line = line.strip()
        
        if not show_explanation:
            if any(keyword in line.lower() for keyword in ['explanation:', 'because', 'this is because', 'the reason', 'note:']):
                in_explanation = True
            if in_explanation:
                continue
        
        cleaned_lines.append(line)
    
    result = '\n'.join(cleaned_lines).strip()
    
    if not show_explanation:
        parts = result.split('\n\n')
        result = parts[0] if parts else result
    
    is_match_question = bool(re.search(r'[A-Z]\s*[→\-]\s*\d', result))
    if is_match_question:
        result = re.sub(r'\s*->\s*', ' → ', result)
        result = re.sub(r'\s*--\s*', ' → ', result)
        result = re.sub(r'â\x86\x92', '→', result)
        result = re.sub(r'â\x80\x99', '→', result)
        lines = result.split('\n')
        match_lines = []
        for line in lines:
            match = re.search(r'([A-Z])\s*→\s*(.+)', line)
            if match:
                letter = match.group(1)
                rest = match.group(2).strip()
                first_sentence = rest.split('.')[0] if '.' in rest else rest
                match_lines.append(f"{letter} → {first_sentence}")
        result = '\n'.join(match_lines) if match_lines else result
    
    return result


def get_ai_response(text_from_ocr: str) -> str:
    """Send OCR text to AI provider and get response."""
    if not text_from_ocr:
        return "No text was extracted from the screenshot."
    
    log_info("Getting AI response for extracted text")
    raw_response = _get_response_from_ai_provider(text_from_ocr)
    return clean_ai_output(raw_response)


def _get_response_from_ai_provider(text_from_ocr: str) -> str:
    """Handle AI API call with optional PDF context."""
    provider = config.get('ai_provider', 'ollama')
    log_info(f"Using AI provider: {provider}")

    pdf_context = ""
    if config.get('use_pdf_context', False):
        pdf_context = load_pdf_context()
        if pdf_context:
            log_info("PDF context loaded successfully")

    if provider == 'ollama':
        return _call_ollama(text_from_ocr, pdf_context)
    elif provider == 'api':
        return _call_external_api(text_from_ocr, pdf_context)
    else:
        return f"Error: Unknown AI provider '{provider}'"


def _call_ollama(text_from_ocr: str, pdf_context: str = "") -> str:
    from .config_manager import load_config
    current_config = load_config()
    api_url = current_config.get('ollama_api_url', 'http://localhost:11434/api/generate')
    model_name = current_config.get('ollama_model', 'deepseek-r1:1.5b')
    prompt_template = current_config.get('prompt_template', 
        "Answer the following question based on your knowledge.\n\nQuestion: [TEXT]")
    
    show_explanation = current_config.get('show_explanation', True)
    if show_explanation:
        prompt_template += "\n\nProvide the correct answer(s) followed by a brief explanation of why it is correct."
    else:
        prompt_template += "\n\nProvide ONLY the correct answer(s), without any explanation or additional text."
    
    prompt = prompt_template.replace("[TEXT]", text_from_ocr)
    
    if pdf_context:
        prompt = f"Use the following reference material to answer the question:\n\n{pdf_context}\n\n{prompt}"
    
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.post(api_url, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            ai_text = data.get("response", "No response from Ollama")
            
            if config.get('debug_mode'):
                from .utils import debug_print
                debug_print("OLLAMA REQUEST", payload)
                debug_print("OLLAMA RESPONSE", data)
            
            return ai_text.strip()
        
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                log_warning(f"Ollama connection failed, retrying ({attempt + 1}/{max_retries})...")
                time.sleep(retry_delay)
                continue
            return f"Error: Cannot connect to Ollama at {api_url}. Is it running?"
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                log_warning(f"Ollama timeout, retrying ({attempt + 1}/{max_retries})...")
                time.sleep(retry_delay)
                continue
            return "Error: Ollama request timed out"
        except requests.exceptions.HTTPError as e:
            return f"Error: Ollama API error {e.response.status_code}"
        except Exception as e:
            log_error(f"Ollama error: {e}", exc_info=True)
            return f"Error: {str(e)}"
    
    return "Error: Maximum retries exceeded"


def _call_external_api(text_from_ocr: str, pdf_context: str = "") -> str:
    from .config_manager import load_config
    current_config = load_config()
    api_url = current_config.get('api_url')
    api_key = current_config.get('api_key')
    model_name = current_config.get('api_model')
    prompt_template = current_config.get('prompt_template',
        "Answer the following question based on your knowledge.\n\nQuestion: [TEXT]")
    
    if not all([api_url, api_key, model_name]):
        return "Error: API configuration incomplete. Check config.json"
    
    show_explanation = current_config.get('show_explanation', True)
    if show_explanation:
        prompt_template += "\n\nProvide the correct answer(s) followed by a brief explanation of why it is correct."
    else:
        prompt_template += "\n\nProvide ONLY the correct answer(s), without any explanation or additional text."
    
    prompt_content = prompt_template.replace("[TEXT]", text_from_ocr)
    
    if pdf_context:
        prompt_content = f"Reference material:\n\n{pdf_context}\n\n{prompt_content}"
    
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt_content}],
        "stream": False
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            ai_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if not ai_text:
                return "Error: Empty response from API"
            
            if config.get('debug_mode'):
                from .utils import debug_print
                debug_print("API REQUEST", {"model": model_name, "prompt_length": len(prompt_content)})
                debug_print("API RESPONSE", {"content_length": len(ai_text)})
            
            return ai_text.strip()
        
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                log_warning(f"API connection failed, retrying ({attempt + 1}/{max_retries})...")
                time.sleep(retry_delay)
                continue
            return f"Error: Cannot connect to API at {api_url}"
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                log_warning(f"API timeout, retrying ({attempt + 1}/{max_retries})...")
                time.sleep(retry_delay)
                continue
            return "Error: API request timed out"
        except requests.exceptions.HTTPError as e:
            if e.response.status_code >= 500 and attempt < max_retries - 1:
                log_warning(f"API server error, retrying ({attempt + 1}/{max_retries})...")
                time.sleep(retry_delay)
                continue
            error_msg = e.response.text
            try:
                error_data = e.response.json()
                error_msg = error_data.get("error", {}).get("message", error_msg)
            except:
                pass
            return f"Error: API error {e.response.status_code} - {error_msg}"
        except Exception as e:
            log_error(f"API error: {e}", exc_info=True)
            return f"Error: {str(e)}"
    
    return "Error: Maximum retries exceeded"