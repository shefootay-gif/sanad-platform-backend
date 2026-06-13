import os
import uuid
import pikepdf

TEMP_DIR = "temp"

async def compress_pdf(file_bytes: bytes, filename: str, compression_level: str = "recommended") -> str:
    """Compresses a PDF file using pikepdf (removes streams/objects not needed)."""
    unique_id = str(uuid.uuid4())
    input_path = os.path.join(TEMP_DIR, f"{unique_id}_input.pdf")
    output_path = os.path.join(TEMP_DIR, f"{unique_id}_compressed.pdf")
    
    with open(input_path, "wb") as f:
        f.write(file_bytes)
        
    try:
        # Load PDF and save with compression options
        with pikepdf.Pdf.open(input_path) as pdf:
            compress_streams = True
            object_stream_mode = pikepdf.ObjectStreamMode.generate
            
            if compression_level == "low":
                compress_streams = False
                object_stream_mode = pikepdf.ObjectStreamMode.disable
                
            pdf.save(
                output_path, 
                compress_streams=compress_streams,
                linearize=True, # Fast web view
                object_stream_mode=object_stream_mode
            )
        return output_path
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

async def split_pdf(file_bytes: bytes, filename: str, ranges: list[int]) -> str:
    """Splits a PDF by extracting specific pages."""
    unique_id = str(uuid.uuid4())
    input_path = os.path.join(TEMP_DIR, f"{unique_id}_input.pdf")
    output_path = os.path.join(TEMP_DIR, f"{unique_id}_split.pdf")
    
    with open(input_path, "wb") as f:
        f.write(file_bytes)
        
    try:
        pdf = pikepdf.Pdf.open(input_path)
        new_pdf = pikepdf.Pdf.new()
        
        # Ranges should be 0-indexed page numbers
        for page_num in ranges:
            if 0 <= page_num < len(pdf.pages):
                new_pdf.pages.append(pdf.pages[page_num])
                
        new_pdf.save(output_path)
        return output_path
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
