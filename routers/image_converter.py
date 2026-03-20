from fastapi import APIRouter, Form, File, UploadFile
from fastapi.responses import StreamingResponse
from PIL import Image
import io

router = APIRouter()

@router.post("/convert-image")
async def convert_image(
    image: UploadFile = File(...),
    format: str = Form(...)
):
    contents = await image.read()
    img = Image.open(io.BytesIO(contents))
    
    if format == "jpeg" and img.mode in ('RGBA', 'LA'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=(img.split()[3] if img.mode == 'RGBA' else None))
        img = background.convert('RGB')
    elif format == "jpeg":
         img = img.convert('RGB')
    
    buf = io.BytesIO()
    if format == "webp":
        img.save(buf, format="WEBP", quality=80)
        media_type = "image/webp"
    else:
        img.save(buf, format="JPEG", quality=85)
        media_type = "image/jpeg"
        
    buf.seek(0)
    return StreamingResponse(buf, media_type=media_type)