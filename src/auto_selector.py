import pyautogui
import time
import random
import re
import pytesseract
from PIL import ImageGrab
from typing import List, Tuple, Optional
from .utils import log_info, log_error, log_warning


class AutoSelector:
    def __init__(self):
        self.enabled = False
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1

    def set_enabled(self, enabled: bool):
        self.enabled = enabled
        log_info(f"Auto-selector {'enabled' if enabled else 'disabled'}")

    def is_enabled(self) -> bool:
        return self.enabled

    def parse_answers(self, ai_response: str) -> Tuple[str, List[str]]:
        lines = [line.strip() for line in ai_response.split('\n') if line.strip()]
        
        if any(re.search(r'[A-Z]\s*→\s*\d', line) for line in lines):
            return 'match', lines
        
        answers = []
        for line in lines:
            line = re.sub(r'^[•\-\*]\s*', '', line)
            if line and not line.lower().startswith(('explanation', 'note:', 'because')):
                answers.append(line)
        
        if len(answers) > 1:
            return 'multiple_choice', answers
        elif len(answers) == 1:
            answer_lower = answers[0].lower()
            if answer_lower in ['true', 'false']:
                return 'true_false', answers
            return 'single_choice', answers
        
        return 'unknown', []

    def find_and_click_answers(self, ai_response: str, screenshot_region: Optional[Tuple[int, int, int, int]] = None):
        if not self.enabled:
            log_info("Auto-selector is disabled, skipping automatic selection")
            return

        question_type, answers = self.parse_answers(ai_response)
        
        try:
            if question_type == 'match':
                log_info("MATCH questions are not supported for auto-selection")
                return
            
            if question_type == 'unknown' or not answers:
                log_warning("Could not determine question type or no answers found")
                return
            
            log_info(f"Detected {question_type} question with {len(answers)} answer(s)")
            
            clicked_positions = []
            for answer in answers:
                clicked_pos = self._click_answer_on_screen(answer, screenshot_region, clicked_positions)
                if clicked_pos:
                    clicked_positions.append(clicked_pos)
                time.sleep(random.uniform(0.3, 0.6))
            
            log_info(f"Successfully selected {len(clicked_positions)} answer(s)")
        
        except Exception as e:
            log_error(f"Error during auto-selection: {e}", exc_info=True)

    def _click_answer_on_screen(self, answer_text: str, region: Optional[Tuple[int, int, int, int]] = None, clicked_positions: List[Tuple[int, int]] = None):
        try:
            clean_answer = re.sub(r'^[©•Oo\-\*\s]+', '', answer_text).strip()
            clean_answer = re.sub(r'^\(e\)\s*', '', clean_answer, flags=re.IGNORECASE)
            clean_answer = re.sub(r'\s+', ' ', clean_answer)
            
            log_info(f"Searching for answer on screen: '{clean_answer}'")
            
            screenshot = ImageGrab.grab(all_screens=True)
            
            try:
                ocr_data = pytesseract.image_to_data(screenshot, output_type=pytesseract.Output.DICT)
                
                best_match = None
                best_match_score = 0
                
                answer_words = clean_answer.lower().split()
                answer_lower = clean_answer.lower()
                
                for i in range(len(ocr_data['text'])):
                    if not ocr_data['text'][i].strip():
                        continue
                    
                    window_texts = []
                    window_indices = []
                    for j in range(max(0, i-2), min(len(ocr_data['text']), i+10)):
                        if ocr_data['text'][j].strip():
                            window_texts.append(ocr_data['text'][j].strip())
                            window_indices.append(j)
                    
                    window_text = ' '.join(window_texts).lower()
                    
                    if len(answer_words) == 1:
                        for idx, word in enumerate(window_texts):
                            if word.lower() == answer_lower:
                                best_match = window_indices[idx]
                                best_match_score = 100
                                break
                    
                    if answer_lower in window_text:
                        exact_match_pos = window_text.find(answer_lower)
                        if exact_match_pos != -1:
                            words_before = window_text[:exact_match_pos].split()
                            target_word_idx = len(words_before)
                            if target_word_idx < len(window_indices):
                                score = 95
                                if score > best_match_score:
                                    best_match = window_indices[min(target_word_idx, len(window_indices)-1)]
                                    best_match_score = score
                    
                    if best_match_score < 90:
                        matched_words = sum(1 for word in answer_words if len(word) > 2 and word in window_text)
                        total_important_words = sum(1 for word in answer_words if len(word) > 2)
                        
                        if total_important_words > 0 and matched_words >= max(2, int(total_important_words * 0.7)):
                            score = (matched_words / max(len(answer_words), 1)) * 85
                            if score > best_match_score:
                                best_match = window_indices[0]
                                best_match_score = score
                
                if best_match is not None and best_match_score > 40:
                    x = ocr_data['left'][best_match]
                    y = ocr_data['top'][best_match] + ocr_data['height'][best_match] // 2
                    
                    radio_x = x - 30
                    
                    if clicked_positions:
                        for prev_x, prev_y in clicked_positions:
                            if abs(radio_x - prev_x) < 20 and abs(y - prev_y) < 20:
                                log_info(f"Skipping duplicate click at ({radio_x}, {y})")
                                return None
                    
                    x_offset = random.randint(-3, 3)
                    y_offset = random.randint(-3, 3)
                    
                    pyautogui.moveTo(radio_x + x_offset, y + y_offset, duration=random.uniform(0.2, 0.4))
                    time.sleep(random.uniform(0.1, 0.2))
                    pyautogui.click()
                    
                    log_info(f"Clicked radio button for answer at ({radio_x}, {y}) with {best_match_score:.1f}% confidence")
                    return (radio_x, y)
                
                log_warning(f"Could not locate answer '{clean_answer}' on screen")
                return None
                
            except Exception as ocr_error:
                log_error(f"OCR detection failed: {ocr_error}")
                log_warning("Auto-select requires visible text on screen")
                return None
            
        except pyautogui.FailSafeException:
            log_error("PyAutoGUI fail-safe triggered - mouse moved to corner")
            raise
        except Exception as e:
            log_error(f"Error in auto-select for '{answer_text}': {e}", exc_info=True)
            return None


_auto_selector_instance = None


def get_auto_selector() -> AutoSelector:
    global _auto_selector_instance
    if _auto_selector_instance is None:
        _auto_selector_instance = AutoSelector()
    return _auto_selector_instance
