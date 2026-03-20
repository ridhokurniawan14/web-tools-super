from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import Response
import fitz  # PyMuPDF
import io

router = APIRouter()

@router.post("/protect-pdf")
async def protect_pdf(
    pdf_file: UploadFile = File(...),
    password: str = Form(...)
):
    try:
        pdf_bytes = await pdf_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        # Proses Enkripsi PDF
        out_buffer = io.BytesIO()
        doc.save(
            out_buffer, 
            encryption=fitz.PDF_ENCRYPT_AES_256, # Enkripsi paling kuat
            user_pw=password,  # Password untuk buka file
            owner_pw=password, # Password untuk hak akses edit
            permissions=fitz.PDF_PERM_PRINT | fitz.PDF_PERM_COPY # User yang tahu password hanya bisa buka, print, dan copy
        )
        doc.close()

        return Response(
            content=out_buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Protected_{pdf_file.filename}"}
        )
    except Exception as e:
        return {"error": f"Gagal memproteksi PDF: {str(e)}"}