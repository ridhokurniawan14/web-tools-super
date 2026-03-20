from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import Response, JSONResponse
import fitz  # PyMuPDF
import io
import os

router = APIRouter()

@router.post("/add-page-numbers")
async def add_page_numbers(
    pdf_file: UploadFile = File(...),
    position: str = Form("bottom_center"), 
    start_num: int = Form(1),
    format_text: str = Form("{n}") # {n} akan diganti jadi angka
):
    try:
        pdf_bytes = await pdf_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        for i, page in enumerate(doc):
            current_num = start_num + i
            text = format_text.replace("{n}", str(current_num))
            
            rect = page.rect
            margin = 30 # Jarak dari pinggir kertas
            fontsize = 12
            
            # Hitung panjang teks agar bisa ke tengah/kanan dengan presisi
            text_length = fitz.get_text_length(text, fontname="Helvetica", fontsize=fontsize)
            
            # Logika Koordinat (X, Y)
            if position == "bottom_center":
                x = (rect.width - text_length) / 2
                y = rect.height - margin
            elif position == "bottom_right":
                x = rect.width - text_length - margin
                y = rect.height - margin
            elif position == "bottom_left":
                x = margin
                y = rect.height - margin
            elif position == "top_center":
                x = (rect.width - text_length) / 2
                y = margin + fontsize
            elif position == "top_right":
                x = rect.width - text_length - margin
                y = margin + fontsize
            elif position == "top_left":
                x = margin
                y = margin + fontsize
            else:
                x = (rect.width - text_length) / 2
                y = rect.height - margin
                
            p = fitz.Point(x, y)
            # Tulis teks berwarna hitam murni (0,0,0)
            page.insert_text(p, text, fontsize=fontsize, fontname="Helvetica", color=(0, 0, 0))

        out_buffer = io.BytesIO()
        doc.save(out_buffer)
        doc.close()

        base_name = pdf_file.filename.rsplit('.', 1)[0]
        return Response(
            content=out_buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Numbered_{base_name}.pdf"}
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Gagal menambah nomor halaman: {str(e)}"})