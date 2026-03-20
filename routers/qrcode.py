from fastapi import APIRouter, Form, File, UploadFile
from fastapi.responses import StreamingResponse
import qrcode
from PIL import Image
import io

router = APIRouter()

@router.post("/generate-qr")
async def generate_qr(
    text: str = Form(...),
    color: str = Form("#000000"),
    bg_color: str = Form("#FFFFFF"),
    logo: UploadFile = File(None)
):
    qr = qrcode.QRCode(
        version=5, 
        error_correction=qrcode.constants.ERROR_CORRECT_H, 
        box_size=10, border=4
    )
    qr.add_data(text)
    qr.make(fit=True)

    img = qr.make_image(fill_color=color, back_color=bg_color).convert('RGB')

    if logo and logo.filename:
        logo_content = await logo.read()
        logo_img = Image.open(io.BytesIO(logo_content))
        img_w, img_h = img.size
        logo_size = int(img_w / 4)
        logo_img = logo_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        pos = ((img_w - logo_size) // 2, (img_h - logo_size) // 2)

        if logo_img.mode in ('RGBA', 'LA') or (logo_img.mode == 'P' and 'transparency' in logo_img.info):
            img.paste(logo_img, pos, logo_img.convert('RGBA'))
        else:
            img.paste(logo_img, pos)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")