from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import Response, JSONResponse
import fitz  # PyMuPDF
import os
import uuid
import io

router = APIRouter()

TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

# 1. Terima PDF dan hitung halamannya
@router.post("/analyze-organize")
async def analyze_organize(pdf_file: UploadFile = File(...)):
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
        return JSONResponse(status_code=500, content={"error": f"Gagal menganalisa PDF: {str(e)}"})

# 2. Kirim thumbnail per halaman
@router.get("/preview-organize-page/{file_id}/{page_index}")
async def preview_organize_page(file_id: str, page_index: int):
    file_path = os.path.join(TEMP_DIR, f"{file_id}.pdf")
    if not os.path.exists(file_path):
        return Response(status_code=404)
    
    doc = fitz.open(file_path)
    if page_index < 0 or page_index >= len(doc):
        doc.close()
        return Response(status_code=400)
        
    page = doc[page_index]
    pix = page.get_pixmap(dpi=40) # Kualitas rendah biar loading ribuan halaman tetap kilat
    img_bytes = pix.tobytes("png")
    doc.close()
    
    return Response(content=img_bytes, media_type="image/png")

# 3. Rakit ulang PDF sesuai susunan user
@router.post("/process-organize")
async def process_organize(
    file_id: str = Form(...), 
    pages: str = Form(...) # Format yang diterima contoh: "0,3,1,5"
):
    try:
        file_path = os.path.join(TEMP_DIR, f"{file_id}.pdf")
        if not os.path.exists(file_path):
            return JSONResponse(status_code=404, content={"error": "File kadaluarsa, silakan upload ulang."})
        
        doc = fitz.open(file_path)
        page_indices = [int(p) for p in pages.split(",")]
        
        new_doc = fitz.open()
        for p in page_indices:
            new_doc.insert_pdf(doc, from_page=p, to_page=p)
            
        out_buffer = io.BytesIO()
        new_doc.save(out_buffer)
        new_doc.close()
        doc.close()
        
        # Bersihkan file sampah
        os.remove(file_path)
        
        return Response(
            content=out_buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=Organized.pdf"}
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Gagal memproses PDF: {str(e)}"})