from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from services import image_service, id_photo_service
import os
import json

router = APIRouter()

def remove_file(path: str):
    if os.path.exists(path):
        os.remove(path)

@router.post("/compress")
async def compress_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    quality: int = Form(70)
):
    file_bytes = await file.read()
    output_path = await image_service.compress_image(file_bytes, file.filename, quality)
    
    # Schedule file cleanup after response is sent
    background_tasks.add_task(remove_file, output_path)
    
    return FileResponse(
        path=output_path, 
        filename=f"compressed_{file.filename}",
        media_type="application/octet-stream"
    )

@router.post("/resize")
async def resize_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    width: int = Form(...),
    height: int = Form(...)
):
    file_bytes = await file.read()
    output_path = await image_service.resize_image(file_bytes, file.filename, width, height)
    
    background_tasks.add_task(remove_file, output_path)
    
    return FileResponse(
        path=output_path, 
        filename=f"resized_{file.filename}",
        media_type="application/octet-stream"
    )

@router.post("/convert")
async def convert_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    target_format: str = Form(...) # e.g. 'webp', 'jpg', 'png'
):
    file_bytes = await file.read()
    output_path = await image_service.convert_image(file_bytes, file.filename, target_format)
    
    background_tasks.add_task(remove_file, output_path)
    
    return FileResponse(
        path=output_path, 
        filename=f"converted.{target_format}",
        media_type="application/octet-stream"
    )

@router.post("/adjust-id-photo")
async def adjust_id_photo(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    remove_bg: bool = Form(False),
    use_smart_crop: bool = Form(False),
    target_width: int = Form(480),
    target_height: int = Form(640),
    bg_color: str = Form("[255, 255, 255]"),
    auto_enhance: bool = Form(False),
    sharpen: bool = Form(False),
    reduce_shadows: bool = Form(False)
):
    file_bytes = await file.read()
    
    # Parse bg_color from JSON string e.g. "[255, 255, 255]"
    parsed_bg_color = tuple(json.loads(bg_color))
    
    output_path = await id_photo_service.process_id_photo(
        file_bytes, 
        file.filename,
        remove_bg=remove_bg,
        use_smart_crop=use_smart_crop,
        target_width=target_width,
        target_height=target_height,
        bg_color=parsed_bg_color,
        auto_enhance=auto_enhance,
        sharpen=sharpen,
        reduce_shadows=reduce_shadows
    )
    
    background_tasks.add_task(remove_file, output_path)
    
    return FileResponse(
        path=output_path, 
        filename=f"id_photo_{file.filename}",
        media_type="image/jpeg"
    )
