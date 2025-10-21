import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from .config_manager import config
from .utils import log_info, log_error


def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    log_info("Preprocessing image for OCR")
    
    width, height = image.size
    if width < 1000 or height < 600:
        scale_factor = 2
        new_size = (width * scale_factor, height * scale_factor)
        image = image.resize(new_size, Image.Resampling.LANCZOS)
        log_info(f"Upscaled image to {new_size}")
    
    processed_image = image.convert('L')
    
    contrast_enhancer = ImageEnhance.Contrast(processed_image)
    processed_image = contrast_enhancer.enhance(1.8)
    
    sharpness_enhancer = ImageEnhance.Sharpness(processed_image)
    processed_image = sharpness_enhancer.enhance(2.0)
    
    processed_image = processed_image.filter(ImageFilter.SHARPEN)
    
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