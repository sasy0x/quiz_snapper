import pytesseract
from PIL import Image, ImageEnhance
from .config_manager import config
from .utils import log_info, log_error


def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    log_info("Preprocessing image for OCR")
    processed_image = image.convert('L')
    enhancer = ImageEnhance.Contrast(processed_image)
    processed_image = enhancer.enhance(1.5)
    return processed_image


def image_to_text(pil_image: Image.Image) -> str:
    if not pil_image:
        log_error("No image provided")
        return ""

    try:
        preprocessed_image = preprocess_image_for_ocr(pil_image)
        languages = config.get('ocr_lang', 'eng')
        log_info(f"Performing OCR with languages: {languages}")
        text = pytesseract.image_to_string(preprocessed_image, lang=languages)
        log_info(f"OCR extracted {len(text)} characters")
        return text.strip()
    except pytesseract.TesseractNotFoundError:
        log_error("Tesseract not found. Please install and add to PATH.")
        raise RuntimeError("TesseractNotFoundError") 
    except Exception as e:
        log_error(f"OCR error: {e}", exc_info=True)
        return ""