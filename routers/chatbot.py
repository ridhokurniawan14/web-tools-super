from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
import google.generativeai as genai

router = APIRouter()

# MASUKKAN API KEY GEMINI KAMU DI SINI
API_KEY = "AIzaSyADxzj_ODiJftwmPRZMF2Cj_lnb6Su13Gc"
genai.configure(api_key=API_KEY)

# Konfigurasi Model AI
generation_config = {
  "temperature": 0.3, # Bikin AI lebih logis, gak gampang halusinasi
  "top_p": 0.9,
  "top_k": 40,
  "max_output_tokens": 1024,
}

# CUCI OTAK AI (SYSTEM INSTRUCTION)
system_instruction = """
Kamu adalah GrisaBot, asisten AI cerdas yang HANYA bertugas memandu pengguna di aplikasi web 'GrisaTools'.
GrisaTools memiliki 12 fitur utilitas di menu sidebar:
1. Custom QR Code
2. Image Converter (Ubah format gambar)
3. Gabung (Merge) PDF
4. Pisah (Split) PDF
5. Organize / Delete PDF (Susun urutan & Hapus halaman PDF)
6. Watermark PDF
7. Protect PDF (Kunci Password)
8. Compress PDF (Kecilkan ukuran)
9. PDF ke Word (.docx)
10. Remove BG Image (Hapus background foto)
11. Compress Image (Kecilkan ukuran MB foto)
12. Beri Nomor Halaman PDF

ATURAN KETAT:
1. Gunakan bahasa Indonesia yang santai, asik, sopan (gunakan sapaan 'bro', 'kak', atau 'teman').
2. TOLAK DENGAN HALUS semua pertanyaan di luar konteks PDF, Gambar, dan QR Code (misal: coding umum, matematika, sejarah, buat puisi). Jawab: "Maaf bro, saya cuma asisten khusus GrisaTools. Saya nggak diajarin hal itu, fokus saya cuma bantuin urusan PDF, Foto, dan dokumen aja nih! ✌️"
3. Jika user menceritakan masalah kompleks, berikan SOLUSI STEP-BY-STEP menggunakan nama fitur yang ada di atas.
Contoh: "Saya mau kasih nomor halaman, tapi ada halaman yang salah, dan filenya belum disatukan".
Jawabanmu harus: "Gampang bro! Ikuti 3 langkah ini di menu sebelah kiri: 1. Buka 'Organize / Delete PDF' buat hapus halaman yang salah. 2. Buka 'Gabung (Merge) PDF' untuk menyatukan filenya. 3. Terakhir, buka 'Beri Nomor Halaman' untuk ngasih nomornya. Langsung sikat bro!"
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=generation_config,
    system_instruction=system_instruction
)

# Simpan histori chat sementara di memori
chat_sessions = {}

@router.post("/chat")
async def chat_with_bot(message: str = Form(...), session_id: str = Form(...)):
    try:
        
        # Buat sesi chat baru jika belum ada
        if session_id not in chat_sessions:
            chat_sessions[session_id] = model.start_chat(history=[])
        
        chat = chat_sessions[session_id]
        response = chat.send_message(message)
        
        return {"reply": response.text}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Bot sedang error: {str(e)}"})