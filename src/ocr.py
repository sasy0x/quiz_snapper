import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import numpy as np
import cv2
from .config_manager import config
from .utils import log_info, log_error


def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    width, height = image.size
    total_pixels = width * height
    log_info(f"Preprocessing image for OCR: {width}x{height} ({total_pixels} pixels)")
    
    if total_pixels < 500000:
        scale_factor = 3.0
        log_info("Small image detected - using aggressive upscaling")
    elif total_pixels < 1000000:
        scale_factor = 2.5
        log_info("Medium image detected - using moderate upscaling")
    elif total_pixels > 4000000:
        scale_factor = 0.7
        log_info("Large image detected - downscaling to optimize OCR")
    else:
        scale_factor = 1.5
        log_info("Optimal size - using light upscaling")
    
    if scale_factor != 1.0:
        new_size = (int(width * scale_factor), int(height * scale_factor))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
        log_info(f"Resized image to {new_size}")
    
    img_array = np.array(image)
    
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
    
    binary = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    kernel = np.ones((1, 1), np.uint8)
    morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    processed_image = Image.fromarray(morph)
    
    contrast_enhancer = ImageEnhance.Contrast(processed_image)
    processed_image = contrast_enhancer.enhance(1.5)
    
    sharpness_enhancer = ImageEnhance.Sharpness(processed_image)
    processed_image = sharpness_enhancer.enhance(1.8)
    
    return processed_image


def image_to_text(pil_image: Image.Image) -> str:
    if not pil_image:
        log_error("No image provided")
        return ""

    try:
        preprocessed_image = preprocess_image_for_ocr(pil_image)
        languages = config.get('ocr_lang', 'eng')
        log_info(f"Performing OCR with languages: {languages}")
        
        custom_config = r'--oem 3 --psm 3'
        text = pytesseract.image_to_string(preprocessed_image, lang=languages, config=custom_config)
        
        log_info(f"OCR extracted {len(text)} characters")
        if text:
            log_info(f"OCR preview: {text[:150]}...")
        return text.strip()
    except pytesseract.TesseractNotFoundError:
        log_error("Tesseract not found. Please install and add to PATH.")
        raise RuntimeError("TesseractNotFoundError") 
    except Exception as e:
        log_error(f"OCR error: {e}", exc_info=True)
        return ""