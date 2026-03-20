from fastapi import APIRouter, File, UploadFile
from fastapi.responses import Response
import fitz  # PyMuPDF
import io
import zipfile
import os
import uuid

router = APIRouter()

TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

@router.post("/analyze-split")
async def analyze_split(pdf_file: UploadFile = File(...)):
    try:
        file_id = str(uuid.uuid4())
        file_path = os.path.join(TEMP_DIR, f"{file_id}.pdf")
        with open(file_path, "wb") as f:
            f.write(await pdf_file.read())
        doc = fitz.open(file_path)
        num_pages = len(doc)
        doc.close()
        return {"id": file_id, "pages": num_pages, "filename": pdf_file.filename}
    except Exception as e:
        return {"error": f"Gagal menganalisa PDF: {str(e)}"}

@router.get("/download-split-all/{file_id}")
async def download_split_all(file_id: str):
    file_path = os.path.join(TEMP_DIR, f"{file_id}.pdf")
    if not os.path.exists(file_path):
        return Response(content="File tidak ditemukan.", status_code=404)
    doc = fitz.open(file_path)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for page_num in range(len(doc)):
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
            page_buffer = io.BytesIO()
            new_doc.save(page_buffer)
            new_doc.close()
            zip_file.writestr(f"Halaman_{page_num + 1}.pdf", page_buffer.getvalue())
    doc.close()
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=Split_PDFs.zip"}
    )

@router.get("/download-split-page/{file_id}/{page_index}")
async def download_split_page(file_id: str, page_index: int):
    file_path = os.path.join(TEMP_DIR, f"{file_id}.pdf")
    if not os.path.exists(file_path):
        return Response(content="File tidak ditemukan.", status_code=404)
    doc = fitz.open(file_path)
    if page_index < 0 or page_index >= len(doc):
        return Response(content="Halaman tidak valid.", status_code=400)
    new_doc = fitz.open()
    new_doc.insert_pdf(doc, from_page=page_index, to_page=page_index)
    page_buffer = io.BytesIO()
    new_doc.save(page_buffer)
    new_doc.close()
    doc.close()
    return Response(
        content=page_buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Halaman_{page_index + 1}.pdf"}
    )

@router.get("/preview-split-page/{file_id}/{page_index}")
async def preview_split_page(file_id: str, page_index: int):
    file_path = os.path.join(TEMP_DIR, f"{file_id}.pdf")
    if not os.path.exists(file_path):
        return Response(content="File tidak ditemukan.", status_code=404)
    doc = fitz.open(file_path)
    if page_index < 0 or page_index >= len(doc):
        doc.close()
        return Response(content="Halaman tidak valid.", status_code=400)
    page = doc[page_index]
    pix = page.get_pixmap(dpi=50) 
    img_bytes = pix.tobytes("png")
    doc.close()
    return Response(content=img_bytes, media_type="image/png")