from fastapi import APIRouter, File, UploadFile
from fastapi.responses import Response, JSONResponse
from typing import List
import fitz  # PyMuPDF
import os
import uuid
import io
import zipfile

router = APIRouter()

TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

@router.post("/compress-pdf-batch")
async def compress_pdf_batch(pdf_files: List[UploadFile] = File(...)):
    try:
        results = []
        for pdf in pdf_files:
            file_id = str(uuid.uuid4())
            raw_bytes = await pdf.read()
            
            doc = fitz.open(stream=raw_bytes, filetype="pdf")
            result_path = os.path.join(TEMP_DIR, f"{file_id}.pdf")
            
            # Kompresi tingkat tinggi (Lossless)
            doc.save(result_path, garbage=4, deflate=True, clean=True)
            doc.close()
            
            compressed_size = os.path.getsize(result_path)
            base_name = pdf.filename.rsplit('.', 1)[0]
            
            results.append({
                "id": file_id,
                "name": f"{base_name}_min.pdf",
                "size": compressed_size
            })
            
        return {"success": True, "files": results}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Gagal mengkompres PDF: {str(e)}"})

@router.get("/download-pdf-comp/{file_id}/{file_name}")
async def download_pdf_comp(file_id: str, file_name: str):
    file_path = os.path.join(TEMP_DIR, f"{file_id}.pdf")
    if not os.path.exists(file_path):
        return Response(status_code=404)
    with open(file_path, "rb") as f:
        return Response(content=f.read(), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={file_name}"})

@router.get("/download-pdf-comp-zip")
async def download_pdf_comp_zip(ids: str):
    file_ids = ids.split(",")
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for idx, fid in enumerate(file_ids):
            result_path = os.path.join(TEMP_DIR, f"{fid}.pdf")
            if os.path.exists(result_path):
                zip_file.write(result_path, arcname=f"Compressed_PDF_{idx+1}.pdf")

    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=Semua_PDF_Dikompres.zip"}
    )