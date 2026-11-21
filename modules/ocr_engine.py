"""
FORMGUARD AI - OCR Engine Module
Handles PDF text extraction and image OCR processing.
"""

import os
import re
from pathlib import Path
from typing import Tuple, List


def extract_text_from_file(file_path: str) -> Tuple[str, float, List[str]]:
    """
    Extract text from a PDF or image file.
    Returns: (extracted_text, confidence, warnings)
    """
    if not os.path.exists(file_path):
        return "", 0.0, [f"File not found: {file_path}"]

    ext = Path(file_path).suffix.lower()
    warnings = []

    if ext == ".pdf":
        text, confidence, pdf_warnings = _extract_from_pdf(file_path)
        warnings.extend(pdf_warnings)
    elif ext in (".jpg", ".jpeg", ".png"):
        text, confidence, img_warnings = _extract_from_image(file_path)
        warnings.extend(img_warnings)
    else:
        return "", 0.0, [f"Unsupported file type: {ext}"]

    # Clean extracted text
    text = _clean_text(text)

    if not text.strip():
        warnings.append("No text could be extracted. The document may be a scanned image requiring OCR.")
        confidence = 0.0

    return text, confidence, warnings


def _extract_from_pdf(file_path: str) -> Tuple[str, float, List[str]]:
    """Extract text from PDF using PyMuPDF."""
    warnings = []
    text = ""
    confidence = 0.0

    try:
        import fitz  # PyMuPDF

        doc = fitz.open(file_path)
        pages_text = []

        for page_num, page in enumerate(doc):
            page_text = page.get_text("text")
            if page_text.strip():
                pages_text.append(page_text)

        doc.close()

        if pages_text:
            text = "\n\n".join(pages_text)
            confidence = 0.85  # PDF text extraction is generally reliable
        else:
            warnings.append("PDF contains no selectable text. It may be a scanned document.")
            # Try OCR on first page image
            text, confidence, ocr_warnings = _ocr_pdf_pages(file_path)
            warnings.extend(ocr_warnings)

    except ImportError:
        warnings.append("PyMuPDF not installed. Install with: pip install PyMuPDF")
        text, confidence = "", 0.0
    except Exception as e:
        warnings.append(f"PDF extraction error: {str(e)}")
        text, confidence = "", 0.0

    return text, confidence, warnings


def _ocr_pdf_pages(file_path: str) -> Tuple[str, float, List[str]]:
    """OCR scanned PDF pages by converting to images."""
    warnings = []
    text = ""
    confidence = 0.0

    try:
        import fitz
        doc = fitz.open(file_path)

        all_text = []
        for page_num in range(min(len(doc), 5)):  # Limit to 5 pages
            page = doc[page_num]
            # Render page as image
            pix = page.get_pixmap(dpi=200)
            img_data = pix.tobytes("png")

            # OCR the image
            page_text, page_conf, page_warnings = _ocr_image_bytes(img_data)
            if page_text:
                all_text.append(page_text)
            warnings.extend(page_warnings)

        doc.close()

        if all_text:
            text = "\n\n".join(all_text)
            confidence = 0.6  # OCR on scanned PDFs is less reliable
        else:
            warnings.append("OCR could not extract text from scanned PDF pages.")

    except Exception as e:
        warnings.append(f"PDF OCR error: {str(e)}")

    return text, confidence, warnings


def _extract_from_image(file_path: str) -> Tuple[str, float, List[str]]:
    """Extract text from image using OCR."""
    warnings = []

    try:
        with open(file_path, "rb") as f:
            img_data = f.read()
        return _ocr_image_bytes(img_data)
    except Exception as e:
        return "", 0.0, [f"Image OCR error: {str(e)}"]


def _ocr_image_bytes(image_bytes: bytes) -> Tuple[str, float, List[str]]:
    """Run OCR on image bytes. Tries Tesseract, then falls back to basic extraction."""
    warnings = []
    text = ""
    confidence = 0.0

    # Try Tesseract
    try:
        import pytesseract
        from PIL import Image
        import io

        img = Image.open(io.BytesIO(image_bytes))

        # Preprocess image for better OCR
        img = _preprocess_image(img)

        # Run Tesseract with config for Indian documents
        custom_config = r'--oem 3 --psm 6 -l eng+hin+mar'
        try:
            text = pytesseract.image_to_string(img, config=custom_config)
        except Exception:
            # Fall back to English only
            text = pytesseract.image_to_string(img)

        if text.strip():
            confidence = 0.7
            # Try to get detailed data with confidence
            try:
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                conf_values = [int(c) for c in data['conf'] if int(c) > 0]
                if conf_values:
                    confidence = sum(conf_values) / len(conf_values) / 100.0
            except Exception:
                pass
        else:
            warnings.append("Tesseract OCR produced no output.")

        return text, confidence, warnings

    except ImportError:
        warnings.append("Tesseract not available. Using fallback extraction.")
    except Exception as e:
        warnings.append(f"Tesseract OCR failed: {str(e)}. Using fallback.")

    # Fallback: Try to extract any embedded text from image metadata
    try:
        from PIL import Image
        import io

        img = Image.open(io.BytesIO(image_bytes))
        # Some images have text in EXIF or metadata
        info = img.info
        if info:
            text = str(info)
            confidence = 0.2
            warnings.append("Only metadata extracted. For better results, install Tesseract OCR.")
    except Exception:
        pass

    if not text:
        warnings.append(
            "No OCR engine available. Install Tesseract: pip install pytesseract "
            "and install Tesseract-OCR on your system."
        )
        confidence = 0.0

    return text, confidence, warnings


def _preprocess_image(img):
    """Preprocess image for better OCR results."""
    try:
        from PIL import Image, ImageFilter, ImageEnhance
        import numpy as np

        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Resize if too small
        width, height = img.size
        if width < 1000:
            scale = 1000 / width
            img = img.resize((int(width * scale), int(height * scale)), Image.LANCZOS)

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)

        # Sharpen
        img = img.filter(ImageFilter.SHARPEN)

        # Convert to grayscale for OCR
        img = img.convert('L')

        # Apply threshold (binarization)
        try:
            import cv2
            img_array = np.array(img)
            _, img_array = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            img = Image.fromarray(img_array)
        except ImportError:
            # Simple threshold without OpenCV
            img = img.point(lambda x: 0 if x < 128 else 255, '1')

        return img

    except Exception:
        return img


def _clean_text(text: str) -> str:
    """Clean extracted text."""
    if not text:
        return ""

    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)

    # Remove null bytes
    text = text.replace('\x00', '')

    # Strip each line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)

    return text.strip()
