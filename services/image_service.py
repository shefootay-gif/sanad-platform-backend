import os
from PIL import Image
import uuid

TEMP_DIR = "temp"

async def compress_image(file_bytes: bytes, filename: str, quality: int = 70) -> str:
    """Compresses an image and returns the path to the compressed file."""
    ext = filename.split('.')[-1].lower()
    if ext not in ['jpg', 'jpeg', 'png', 'webp']:
        ext = 'jpg'
        
    unique_id = str(uuid.uuid4())
    input_path = os.path.join(TEMP_DIR, f"{unique_id}_input.{ext}")
    output_path = os.path.join(TEMP_DIR, f"{unique_id}_compressed.{ext}")
    
    # Save input temporarily
    with open(input_path, "wb") as f:
        f.write(file_bytes)
        
    try:
        with Image.open(input_path) as img:
            # Convert RGBA to RGB if saving as JPEG
            if img.mode in ("RGBA", "P") and ext in ("jpg", "jpeg"):
                img = img.convert("RGB")
            
            # Save with reduced quality
            img.save(output_path, quality=quality, optimize=True)
            
        return output_path
    finally:
        # Cleanup input
        if os.path.exists(input_path):
            os.remove(input_path)

async def resize_image(file_bytes: bytes, filename: str, width: int, height: int) -> str:
    """Resizes an image and returns the path to the resized file."""
    ext = filename.split('.')[-1].lower()
    unique_id = str(uuid.uuid4())
    input_path = os.path.join(TEMP_DIR, f"{unique_id}_input.{ext}")
    output_path = os.path.join(TEMP_DIR, f"{unique_id}_resized.{ext}")
    
    with open(input_path, "wb") as f:
        f.write(file_bytes)
        
    try:
        with Image.open(input_path) as img:
            resized_img = img.resize((width, height), Image.Resampling.LANCZOS)
            resized_img.save(output_path)
        return output_path
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

async def convert_image(file_bytes: bytes, filename: str, target_format: str) -> str:
    """Converts an image to a new format."""
    ext = filename.split('.')[-1].lower()
    target_format = target_format.lower()
    
    # PIL mapping
    format_map = {
        'jpg': 'JPEG',
        'jpeg': 'JPEG',
        'png': 'PNG',
        'webp': 'WEBP',
        'gif': 'GIF'
    }
    
    pil_format = format_map.get(target_format, 'JPEG')
    
    unique_id = str(uuid.uuid4())
    input_path = os.path.join(TEMP_DIR, f"{unique_id}_input.{ext}")
    output_path = os.path.join(TEMP_DIR, f"{unique_id}_converted.{target_format}")
    
    with open(input_path, "wb") as f:
        f.write(file_bytes)
        
    try:
        with Image.open(input_path) as img:
            if img.mode in ("RGBA", "P") and pil_format == "JPEG":
                img = img.convert("RGB")
            img.save(output_path, format=pil_format)
        return output_path
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
