from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import Response
from PIL import Image as PILImage
import fitz  # PyMuPDF
import io

router = APIRouter()

@router.post("/watermark-pdf")
async def watermark_pdf(
    pdf_file: UploadFile = File(...),
    wm_type: str = Form(...),
    text: str = Form(""),
    image: UploadFile = File(None),
    rotation: int = Form(0)
):
    try:
        pdf_bytes = await pdf_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        pil_img = None

        # --- LANGKAH 1: SIAPKAN GAMBAR WATERMARK ---
        if wm_type == "image" and image:
            # Jika user upload logo, langsung baca sebagai gambar
            raw_img = await image.read()
            pil_img = PILImage.open(io.BytesIO(raw_img)).convert("RGBA")
            
        elif wm_type == "text" and text:
            # TRIK SAKTI: Jika user input teks, kita "foto" teksnya jadi gambar transparan
            fontsize = 80 # Ukuran besar biar resolusinya HD
            text_length = fitz.get_text_length(text, fontname="Helvetica-Bold", fontsize=fontsize)
            
            # Buat kanvas PDF kosong sementara sebesar teksnya
            temp_doc = fitz.open()
            temp_page = temp_doc.new_page(width=text_length + 20, height=fontsize + 40)
            
            # Tulis teksnya dengan warna hitam pekat (Transparansinya diatur nanti)
            temp_page.insert_text(fitz.Point(10, fontsize + 10), text, fontsize=fontsize, fontname="Helvetica-Bold", color=(0, 0, 0))
            
            # Render kanvas tadi menjadi gambar PNG transparan
            pix = temp_page.get_pixmap(alpha=True, dpi=150)
            img_bytes = pix.tobytes("png")
            temp_doc.close()

            # Jadikan sebagai objek Pillow Image
            pil_img = PILImage.open(io.BytesIO(img_bytes)).convert("RGBA")

        # --- LANGKAH 2: ROTASI & TRANSPARANSI (UNTUK TEKS MAUPUN LOGO) ---
        final_img_bytes = None
        if pil_img:
            # Putar gambar berapapun derajatnya (anti error)
            if rotation != 0:
                pil_img = pil_img.rotate(-rotation, expand=True)
            
            # Berikan efek transparan (Opacity 30%)
            alpha = pil_img.split()[3]
            alpha = alpha.point(lambda p: p * 0.3)
            pil_img.putalpha(alpha)
            
            # Simpan hasil olahan ke memori
            img_io = io.BytesIO()
            pil_img.save(img_io, format="PNG")
            final_img_bytes = img_io.getvalue()
            pil_w, pil_h = pil_img.size

        # --- LANGKAH 3: TEMPEL KE PDF ---
        if final_img_bytes:
            for page in doc:
                rect = page.rect
                
                # Hitung rasio agar watermark tidak lebih besar dari 80% ukuran halaman (biar rapi)
                ratio = min((rect.width * 0.8) / pil_w, (rect.height * 0.8) / pil_h)
                new_w = pil_w * ratio
                new_h = pil_h * ratio
                
                # Cari titik koordinat tengah persis
                x0 = (rect.width - new_w) / 2
                y0 = (rect.height - new_h) / 2
                img_rect = fitz.Rect(x0, y0, x0 + new_w, y0 + new_h)
                
                # Tempel ke tengah halaman!
                page.insert_image(img_rect, stream=final_img_bytes, keep_proportion=True)

        # Siapkan untuk di-download
        out_buffer = io.BytesIO()
        doc.save(out_buffer)
        doc.close()

        return Response(
            content=out_buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=Watermarked.pdf"}
        )
    except Exception as e:
        return {"error": f"Gagal menambahkan watermark: {str(e)}"}