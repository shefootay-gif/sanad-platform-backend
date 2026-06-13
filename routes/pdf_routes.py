from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from services import pdf_service
import os
import json

router = APIRouter()

def remove_file(path: str):
    if os.path.exists(path):
        os.remove(path)

@router.post("/compress")
async def compress_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    compression_level: str = Form("recommended")
):
    file_bytes = await file.read()
    output_path = await pdf_service.compress_pdf(file_bytes, file.filename, compression_level)
    
    background_tasks.add_task(remove_file, output_path)
    
    return FileResponse(
        path=output_path, 
        filename=f"compressed_{file.filename}",
        media_type="application/pdf"
    )

@router.post("/split")
async def split_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    pages: str = Form(...) # Expects JSON array string e.g. "[0, 1, 2]"
):
    file_bytes = await file.read()
    ranges = json.loads(pages)
    
    output_path = await pdf_service.split_pdf(file_bytes, file.filename, ranges)
    
    background_tasks.add_task(remove_file, output_path)
    
    return FileResponse(
        path=output_path, 
        filename=f"split_{file.filename}",
        media_type="application/pdf"
    )
