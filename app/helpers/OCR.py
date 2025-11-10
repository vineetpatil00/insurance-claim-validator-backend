# import easyocr
# from pdf2image import convert_from_bytes
# from PIL import Image
# import io
# from typing import Optional
# import numpy as np

import os
import base64
import httpx
from pdf2image import convert_from_bytes
from PIL import Image
import io
from dotenv import load_dotenv

load_dotenv()

# # Initialize EasyOCR reader (lazy initialization)
# _reader = None

# def get_reader():
#     """Get or create EasyOCR reader instance."""
#     global _reader
#     if _reader is None:
#         # Initialize with English and common Indian languages
#         _reader = easyocr.Reader(['en'], gpu=False)
#     return _reader

def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """
    Extract text from PDF or image file using Groq Vision model.
    
    Args:
        file_bytes: File content as bytes
        filename: Name of the file
        
    Returns:
        Extracted text string
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise Exception("GROQ_API_KEY environment variable is not set")
    
    text = ""
    
    try:
        # Convert PDF to images if needed
        images = []
        if filename.lower().endswith(".pdf"):
            # Convert PDF pages to images
            pages = convert_from_bytes(file_bytes)
            for page in pages:
                # Convert PIL Image to bytes
                img_buffer = io.BytesIO()
                page.save(img_buffer, format='PNG')
                images.append(img_buffer.getvalue())
        else:
            # For image files, use directly
            images = [file_bytes]
        
        # Process each image with Groq Vision
        for image_bytes in images:
            # Encode image to base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Prepare the request for Groq Vision API
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract all text from this image. Return the text exactly as it appears, preserving formatting and structure. Include all visible text including headers, labels, values, and any other text content."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 4096
            }
            
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    page_text = result["choices"][0]["message"]["content"]
                    text += page_text + "\n"
        
        return text.strip()
        
    except httpx.HTTPStatusError as e:
        raise Exception(f"Groq Vision API error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        raise Exception(f"Text extraction failed: {str(e)}")

