from fastapi import APIRouter, File, UploadFile
from fastapi.responses import Response, JSONResponse
from typing import List
from pdf2docx import Converter
import os
import uuid
import io
import zipfile

router = APIRouter()

TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

# Endpoint A: Proses Konversi Banyak File
@router.post("/pdf-to-word-batch")
async def pdf_to_word_batch(pdf_files: List[UploadFile] = File(...)):
    try:
        results = []
        
        for pdf_file in pdf_files:
            file_id = str(uuid.uuid4())
            pdf_path = os.path.join(TEMP_DIR, f"{file_id}.pdf")
            docx_path = os.path.join(TEMP_DIR, f"{file_id}.docx")

            # 1. Simpan PDF sementara
            with open(pdf_path, "wb") as f:
                f.write(await pdf_file.read())

            # 2. Proses Konversi
            cv = Converter(pdf_path)
            cv.convert(docx_path)
            cv.close()

            # 3. Hapus PDF asli biar hemat memori server
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

            # 4. Simpan data untuk dikembalikan ke Frontend
            original_name = os.path.splitext(pdf_file.filename)[0]
            docx_name = f"{original_name}.docx"
            results.append({
                "id": file_id,
                "name": docx_name
            })

        return {"success": True, "files": results}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Gagal mengkonversi PDF: {str(e)}"})

# Endpoint B: Download Satuan
@router.get("/download-word/{file_id}")
async def download_word(file_id: str):
    docx_path = os.path.join(TEMP_DIR, f"{file_id}.docx")
    if not os.path.exists(docx_path):
        return Response(content="File tidak ditemukan.", status_code=404)

    with open(docx_path, "rb") as f:
        docx_bytes = f.read()

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=Converted_{file_id[-4:]}.docx"}
    )

# Endpoint C: Download Semua via ZIP
@router.get("/download-word-zip")
async def download_word_zip(ids: str):
    file_ids = ids.split(",")
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for idx, fid in enumerate(file_ids):
            docx_path = os.path.join(TEMP_DIR, f"{fid}.docx")
            if os.path.exists(docx_path):
                # Masukkan ke dalam ZIP dengan nama urut
                zip_file.write(docx_path, arcname=f"Dokumen_Word_{idx+1}.docx")

    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=Semua_Word_Converted.zip"}
    )