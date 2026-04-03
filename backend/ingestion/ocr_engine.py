"""
ScholarGraph AI — OCR Engine
Tesseract OCR wrapper for extracting text from scanned documents and images.
Includes image preprocessing for improved accuracy.
"""

import io
from typing import Optional
from PIL import Image, ImageFilter, ImageEnhance


class OCREngine:
    """
    Tesseract OCR wrapper with image preprocessing pipeline.
    
    Preprocessing steps:
    1. Convert to grayscale
    2. Enhance contrast
    3. Apply slight sharpening
    4. Resize if too small
    """

    def __init__(self, lang: str = "eng", config: str = "--oem 3 --psm 6"):
        """
        Initialize OCR engine.
        
        Args:
            lang: Tesseract language code
            config: Tesseract configuration string
        """
        self.lang = lang
        self.config = config

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Apply preprocessing to improve OCR accuracy.
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image
        """
        # Convert to grayscale
        if image.mode != "L":
            image = image.convert("L")

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)

        # Sharpen
        image = image.filter(ImageFilter.SHARPEN)

        # Resize if too small (minimum 300 DPI equivalent)
        min_width = 1000
        if image.width < min_width:
            ratio = min_width / image.width
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.LANCZOS)

        return image

    def extract_from_image(self, image_path: str) -> str:
        """
        Extract text from an image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text string
        """
        try:
            import pytesseract
            image = Image.open(image_path)
            processed = self._preprocess_image(image)
            text = pytesseract.image_to_string(processed, lang=self.lang, config=self.config)
            return text.strip()
        except ImportError:
            return "[OCR unavailable: pytesseract not installed]"
        except Exception as e:
            return f"[OCR error: {str(e)}]"

    def extract_from_bytes(self, image_bytes: bytes) -> Optional[str]:
        """
        Extract text from image bytes (e.g., rendered PDF page).
        
        Args:
            image_bytes: Raw image bytes (PNG format)
            
        Returns:
            Extracted text or None on failure
        """
        try:
            import pytesseract
            image = Image.open(io.BytesIO(image_bytes))
            processed = self._preprocess_image(image)
            text = pytesseract.image_to_string(processed, lang=self.lang, config=self.config)
            return text.strip() if text.strip() else None
        except ImportError:
            return None
        except Exception:
            return None

    def extract_from_pil(self, image: Image.Image) -> str:
        """Extract text from a PIL Image object directly."""
        try:
            import pytesseract
            processed = self._preprocess_image(image)
            text = pytesseract.image_to_string(processed, lang=self.lang, config=self.config)
            return text.strip()
        except ImportError:
            return "[OCR unavailable: pytesseract not installed]"
        except Exception as e:
            return f"[OCR error: {str(e)}]"
