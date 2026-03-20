from fastapi import APIRouter, File, UploadFile
from fastapi.responses import Response, JSONResponse
from typing import List
import os
import uuid
import io
import zipfile

router = APIRouter()

TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

@router.post("/remove-bg-batch")
async def remove_bg_batch(images: List[UploadFile] = File(...)):
    try:
        # Panggil library di dalam sini agar server tidak hang saat menyala
        from rembg import remove, new_session
        
        # KUNCI KECEPATAN: Gunakan model 'u2netp' (versi ringan, sangat cepat di CPU)
        session = new_session("u2netp")
        
        results = []
        for img in images:
            file_id = str(uuid.uuid4())
            orig_path = os.path.join(TEMP_DIR, f"{file_id}_orig.png")
            result_path = os.path.join(TEMP_DIR, f"{file_id}_res.png")
            
            # 1. Baca dan simpan gambar asli
            input_bytes = await img.read()
            with open(orig_path, "wb") as f:
                f.write(input_bytes)
            
            # 2. Proses Hapus Background Super Cepat
            output_bytes = remove(input_bytes, session=session)
            with open(result_path, "wb") as f:
                f.write(output_bytes)
                
            base_name = img.filename.rsplit('.', 1)[0]
            results.append({
                "id": file_id,
                "name": base_name
            })
            
        return {"success": True, "files": results}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Gagal menghapus background: {str(e)}"})

# Endpoint ambil gambar untuk Preview Before/After
@router.get("/get-bg-image/{file_id}/{img_type}")
async def get_bg_image(file_id: str, img_type: str):
    suffix = "_orig.png" if img_type == "original" else "_res.png"
    file_path = os.path.join(TEMP_DIR, f"{file_id}{suffix}")
    
    if not os.path.exists(file_path):
        return Response(status_code=404)
        
    with open(file_path, "rb") as f:
        return Response(content=f.read(), media_type="image/png")

# Endpoint Download ZIP
@router.get("/download-bg-zip")
async def download_bg_zip(ids: str):
    file_ids = ids.split(",")
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for idx, fid in enumerate(file_ids):
            result_path = os.path.join(TEMP_DIR, f"{fid}_res.png")
            if os.path.exists(result_path):
                zip_file.write(result_path, arcname=f"NoBG_Image_{idx+1}.png")

    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=Semua_NoBG.zip"}
    )