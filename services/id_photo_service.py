import os
from PIL import Image, ExifTags, ImageEnhance, ImageFilter
import numpy as np
import uuid

try:
    from rembg import remove, new_session
    import mediapipe as mp
except ImportError:
    pass

import cv2

TEMP_DIR = "temp"

def apply_background_removal(img, bg_color=(255, 255, 255)):
    try:
        session = new_session("u2net_human_seg")
        output = remove(img, session=session, post_process_mask=True, alpha_matting=True, alpha_matting_foreground_threshold=240, alpha_matting_background_threshold=10, alpha_matting_erode_size=10)
        if output.mode in ("RGBA", "LA") or (output.mode == "P" and "transparency" in output.info):
            bg_img = Image.new("RGB", output.size, bg_color)
            bg_img.paste(output, mask=output.split()[3])
            return bg_img
        else:
            return output.convert("RGB")
    except Exception as e:
        print(f"Background removal failed: {e}")
        return img

def smart_face_crop(img, target_ratio):
    try:
        mp_face_detection = mp.solutions.face_detection
        
        img_cv = np.array(img.convert('RGB'))
        img_cv = img_cv[:, :, ::-1].copy() 
        
        with mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5) as face_detection:
            results = face_detection.process(img_cv)
            
            width, height = img.size
            if not results.detections:
                return default_crop(img, target_ratio)
            
            detection = results.detections[0]
            bboxC = detection.location_data.relative_bounding_box
            
            fx = int(bboxC.xmin * width)
            fy = int(bboxC.ymin * height)
            fw = int(bboxC.width * width)
            fh = int(bboxC.height * height)
            
            face_center_x = fx + fw // 2
            
            crop_width = int(fw * 2.5)
            crop_height = int(crop_width / target_ratio)
            
            xmin = face_center_x - crop_width // 2
            ymin = fy - int(crop_height * 0.2)
            
            xmax = xmin + crop_width
            ymax = ymin + crop_height
            
            if xmin < 0:
                xmax -= xmin
                xmin = 0
            if ymin < 0:
                ymax -= ymin
                ymin = 0
            if xmax > width:
                xmin -= (xmax - width)
                xmax = width
            if ymax > height:
                ymin -= (ymax - height)
                ymax = height
                
            xmin = max(0, xmin)
            ymin = max(0, ymin)
                
            return img.crop((xmin, ymin, xmax, ymax))

    except Exception as e:
        print(f"Smart crop failed: {e}")
        return default_crop(img, target_ratio)

def default_crop(img, target_ratio):
    width, height = img.size
    img_ratio = width / height
    if img_ratio > target_ratio:
        new_width = int(target_ratio * height)
        offset = (width - new_width) / 2
        return img.crop((offset, 0, width - offset, height))
    elif img_ratio < target_ratio:
        new_height = int(width / target_ratio)
        offset_y = max(0, (height - new_height) * 0.2)
        return img.crop((0, offset_y, width, offset_y + new_height))
    return img

def apply_auto_enhance(img):
    try:
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)
        return img
    except Exception as e:
        print(f"Enhance failed: {e}")
        return img

def apply_sharpen(img):
    try:
        return img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
    except Exception as e:
        print(f"Sharpen failed: {e}")
        return img

def apply_shadow_reduction(img):
    try:
        img_cv = np.array(img.convert('RGB'))
        lab = cv2.cvtColor(img_cv, cv2.COLOR_RGB2LAB)
        l_channel, a, b = cv2.split(lab)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        cl = clahe.apply(l_channel)
        
        limg = cv2.merge((cl, a, b))
        result_cv = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)
        return Image.fromarray(result_cv)
    except Exception as e:
        print(f"Shadow reduction failed: {e}")
        return img

async def process_id_photo(
    file_bytes: bytes, 
    filename: str, 
    remove_bg: bool = False, 
    use_smart_crop: bool = False, 
    target_width: int = 480, 
    target_height: int = 640, 
    bg_color: tuple = (255, 255, 255), 
    auto_enhance: bool = False, 
    sharpen: bool = False, 
    reduce_shadows: bool = False
) -> str:
    """Processes an ID photo and returns the path to the resulting file."""
    unique_id = str(uuid.uuid4())
    input_path = os.path.join(TEMP_DIR, f"{unique_id}_input.jpg")
    output_path = os.path.join(TEMP_DIR, f"{unique_id}_id_photo.jpg")
    
    with open(input_path, "wb") as f:
        f.write(file_bytes)
        
    try:
        target_ratio = target_width / target_height

        img = Image.open(input_path)
        
        # Handle EXIF orientation
        try:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break
            exif = img._getexif()
            if exif is not None:
                orientation_val = exif.get(orientation, None)
                if orientation_val == 3:
                    img = img.rotate(180, expand=True)
                elif orientation_val == 6:
                    img = img.rotate(270, expand=True)
                elif orientation_val == 8:
                    img = img.rotate(90, expand=True)
        except (AttributeError, KeyError, IndexError):
            pass

        # Cropping
        if use_smart_crop:
            img = smart_face_crop(img, target_ratio)
            img = default_crop(img, target_ratio)
        else:
            img = default_crop(img, target_ratio)
            
        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

        # Apply Background Removal
        if remove_bg:
            img = apply_background_removal(img, bg_color=bg_color)
            
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            bg_img = Image.new("RGB", img.size, bg_color)
            bg_img.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
            img = bg_img
        elif img.mode != "RGB":
            img = img.convert("RGB")
            
        if auto_enhance:
            img = apply_auto_enhance(img)
            
        if reduce_shadows:
            img = apply_shadow_reduction(img)
            
        if sharpen:
            img = apply_sharpen(img)

        quality = 95
        max_size = 1000 * 1024 
        
        while quality > 20:
            img.save(output_path, "JPEG", quality=quality, optimize=True)
            if os.path.getsize(output_path) <= max_size:
                break
            quality -= 5
            
        return output_path
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
