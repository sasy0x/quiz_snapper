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
    
    result = raw_response
    
    result = re.sub(r'<[^>]*>', '', result)
    result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)
    result = re.sub(r'â\x86\x92', '→', result)
    result = re.sub(r'â†’', '→', result)
    result = re.sub(r'â\x80\x93', '-', result)
    result = re.sub(r'â\x80\x94', '—', result)
    result = re.sub(r'â\x80\x98', "'", result)
    result = re.sub(r'â\x80\x99', "'", result)
    result = re.sub(r'â\x80\x9c', '"', result)
    result = re.sub(r'â\x80\x9d', '"', result)
    
    lines = result.split('\n')
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
    
    potential_matches = re.findall(r'([A-Z])\s*[→\-]>\s*(.+?)(?=\s*[A-Z]\s*[→\-]>|$)', result)
    is_match_question = len(potential_matches) >= 3
    
    if is_match_question:
        log_info(f"Detected MATCHING question with {len(potential_matches)} pairs, formatting...")
        
        match_dict = {}
        for letter, description in potential_matches:
            description = description.strip()
            description = re.sub(r'[,;\.\s]+$', '', description)
            if len(description) > 5:
                match_dict[letter] = description
                log_info(f"Extracted: {letter} → {description[:60]}")
        
        if len(match_dict) >= 3:
            formatted_lines = []
            formatted_lines.append("\n=== MATCHING PAIRS ===")
            for letter in sorted(match_dict.keys()):
                formatted_lines.append(f"[{letter}] matches with: {match_dict[letter]}")
            formatted_lines.append("=====================\n")
            result = '\n'.join(formatted_lines)
            log_info(f"Formatted {len(match_dict)} matching pairs")
        else:
            log_info("Not enough valid pairs, treating as normal question")
            is_match_question = False
    
    return result


def get_ai_response(text_from_ocr: str) -> str:
    if not text_from_ocr:
        log_error("No OCR text provided to AI")
        return "No text was extracted from the screenshot."
    
    log_info(f"OCR Input ({len(text_from_ocr)} chars): {text_from_ocr[:200]}...")
    raw_response = _get_response_from_ai_provider(text_from_ocr)
    log_info(f"Raw AI Response: {raw_response[:300]}...")
    
    cleaned = clean_ai_output(raw_response)
    log_info(f"Cleaned Output: {cleaned}")
    
    return cleaned


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
        prompt_template += "\n\nProvide the correct answer(s) followed by a brief explanation."
    else:
        if 'match' in text_from_ocr.lower() or 'pair' in text_from_ocr.lower():
            prompt_template += "\n\nMATCHING QUESTION - Critical Instructions:\n1. Read the ENTIRE question carefully\n2. Identify what needs to be matched (left column vs right column)\n3. For EACH letter (A, B, C, D, etc.), determine the CORRECT match\n4. Format EXACTLY as: 'A -> complete description', 'B -> complete description', etc.\n5. Each match on a separate line\n6. Think logically about relationships and definitions\n7. Do NOT include special tokens, explanations, or metadata\n8. ONLY provide the final matching pairs"
        else:
            prompt_template += "\n\nReturn ONLY the exact text of the correct answer(s) as shown in the options. For multiple answers, list each on a new line with a dash (-)."
    
    prompt = prompt_template.replace("[TEXT]", text_from_ocr)
    
    log_info(f"Ollama prompt length: {len(prompt)} chars")
    
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
            
            ai_text = re.sub(r'<\|.*?\|>', '', ai_text)
            ai_text = re.sub(r'<think>.*?</think>', '', ai_text, flags=re.DOTALL)
            
            log_info(f"Ollama response received: {len(ai_text)} chars")
            
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
        log_error("API configuration incomplete")
        return "Error: API configuration incomplete. Check config.json"
    
    show_explanation = current_config.get('show_explanation', True)
    if show_explanation:
        prompt_template += "\n\nProvide the correct answer(s) followed by a brief explanation."
    else:
        if 'match' in text_from_ocr.lower() or 'pair' in text_from_ocr.lower():
            prompt_template += "\n\nMATCHING QUESTION - Critical Instructions:\n1. Read the ENTIRE question carefully\n2. Identify what needs to be matched (left column vs right column)\n3. For EACH letter (A, B, C, D, etc.), determine the CORRECT match\n4. Format EXACTLY as: 'A -> complete description', 'B -> complete description', etc.\n5. Each match on a separate line\n6. Think logically about relationships and definitions\n7. Do NOT include special tokens, explanations, or metadata\n8. ONLY provide the final matching pairs"
        else:
            prompt_template += "\n\nReturn ONLY the exact text of the correct answer(s) as shown in the options. For multiple answers, list each on a new line with a dash (-)."
    
    prompt_content = prompt_template.replace("[TEXT]", text_from_ocr)
    
    log_info(f"API: {api_url}, Model: {model_name}, Prompt length: {len(prompt_content)}")
    
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
                log_error("Empty response from API")
                return "Error: Empty response from API"
            
            log_info(f"API response received: {len(ai_text)} chars")
            
            if config.get('debug_mode'):
                from .utils import debug_print
                debug_print("API REQUEST", {"model": model_name, "prompt_length": len(prompt_content)})
                debug_print("API RESPONSE", {"content_length": len(ai_text), "content": ai_text[:500]})
            
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