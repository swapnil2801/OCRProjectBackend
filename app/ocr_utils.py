import pytesseract
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from PIL import Image
import io
import os
import fitz  # PyMuPDF
import pdfplumber


# Only needed on Windows:
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\swapnil.patil\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"


# Simple PDF extraction (searchable PDFs)
def extract_text_simple_pdf(pdf_bytes: bytes) -> str:
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    return text


# Scanned PDF OCR using PyMuPDF
def extract_text_scanned_pdf(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = []

    for page_number in range(len(doc)):
        page = doc.load_page(page_number)

        # Render page → image
        pix = page.get_pixmap(dpi=300)
        img_bytes = pix.tobytes("png")

        img = Image.open(io.BytesIO(img_bytes))
        text = pytesseract.image_to_string(img)

        full_text.append(text)

    return "\n".join(full_text)


# OCR for images (jpg/png/jpeg)
def extract_text_from_image(img_bytes: bytes) -> str:
    img = Image.open(io.BytesIO(img_bytes))
    return pytesseract.image_to_string(img)


# Auto detect type (PDF or image)
def auto_detect_ocr(file_bytes: bytes, filename: str) -> str:
    ext = filename.lower()

    if ext.endswith(".pdf"):
        # Try simple text first
        text = extract_text_simple_pdf(file_bytes)
        if text.strip():
            return text
        return extract_text_scanned_pdf(file_bytes)

    # Otherwise treat as image
    return extract_text_from_image(file_bytes)