from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import Response, JSONResponse
from typing import List
from PIL import Image as PILImage
import os
import uuid
import io
import zipfile

router = APIRouter()

TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

@router.post("/compress-image-batch")
async def compress_image_batch(
    images: List[UploadFile] = File(...),
    quality: int = Form(60) # Default kualitas 60%
):
    try:
        results = []
        for img in images:
            file_id = str(uuid.uuid4())
            raw_bytes = await img.read()
            
            # Buka gambar menggunakan Pillow
            pil_img = PILImage.open(io.BytesIO(raw_bytes))
            
            # Konversi palet warna agar aman saat disimpan
            if pil_img.mode in ("RGBA", "P"):
                # Buat background putih murni untuk gambar transparan jika dikompres
                background = PILImage.new('RGBA', pil_img.size, (255, 255, 255))
                pil_img = PILImage.alpha_composite(background, pil_img).convert("RGB")
            else:
                pil_img = pil_img.convert("RGB")
            
            # Simpan ke memori sementara dengan optimasi tingkat tinggi
            result_path = os.path.join(TEMP_DIR, f"{file_id}.webp")
            pil_img.save(result_path, format="WEBP", quality=quality, optimize=True)
            
            # Dapatkan ukuran file setelah dikompres
            compressed_size = os.path.getsize(result_path)
            base_name = img.filename.rsplit('.', 1)[0]
            
            results.append({
                "id": file_id,
                "name": f"{base_name}_min.webp",
                "size": compressed_size
            })
            
        return {"success": True, "files": results}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Gagal mengkompres gambar: {str(e)}"})

@router.get("/download-img-comp/{file_id}/{file_name}")
async def download_img_comp(file_id: str, file_name: str):
    file_path = os.path.join(TEMP_DIR, f"{file_id}.webp")
    if not os.path.exists(file_path):
        return Response(status_code=404)
    with open(file_path, "rb") as f:
        return Response(content=f.read(), media_type="image/webp", headers={"Content-Disposition": f"attachment; filename={file_name}"})

@router.get("/download-img-comp-zip")
async def download_img_comp_zip(ids: str):
    file_ids = ids.split(",")
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for idx, fid in enumerate(file_ids):
            result_path = os.path.join(TEMP_DIR, f"{fid}.webp")
            if os.path.exists(result_path):
                zip_file.write(result_path, arcname=f"Compressed_Image_{idx+1}.webp")

    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=Semua_Gambar_Dikompres.zip"}
    )