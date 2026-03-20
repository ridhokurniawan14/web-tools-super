from fastapi import APIRouter, File, UploadFile
from fastapi.responses import Response
from typing import List
import fitz  # PyMuPDF
import io

router = APIRouter()

@router.post("/merge-pdfs")
async def merge_pdfs(pdf_files: List[UploadFile] = File(...)):
    try:
        merged_doc = fitz.open()
        for pdf in pdf_files:
            pdf_bytes = await pdf.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            merged_doc.insert_pdf(doc)
            
        out_buffer = io.BytesIO()
        merged_doc.save(out_buffer)
        merged_doc.close()
        
        return Response(
            content=out_buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=Merged_Result.pdf"}
        )
    except Exception as e:
        return {"error": f"Gagal menggabungkan PDF: {str(e)}"}