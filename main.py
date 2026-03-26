from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import os
import time

# Import semua router
from routers import (
    qrcode, image_converter, pdf_merge, pdf_split, 
    pdf_watermark, pdf_protect, pdf_compress, pdf_to_word, 
    remove_bg, image_compressor, pdf_organize, pdf_page_numbers, chatbot
)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ==========================================
# MIDDLEWARE ANTI-SPAM (THROTTLE)
# ==========================================
ip_request_tracker = {}

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # KUNCI PERBAIKAN: Bebaskan request GET (Load halaman web) dari tilangan
    if request.method == "GET":
        return await call_next(request)

    client_ip = request.client.host
    current_time = time.time()
    
    # Bersihkan memori dari IP yang requestnya sudah lebih dari 60 detik (1 menit) yang lalu
    if client_ip in ip_request_tracker:
        ip_request_tracker[client_ip] = [t for t in ip_request_tracker[client_ip] if current_time - t < 60]
    else:
        ip_request_tracker[client_ip] = []

    # BATAS: 30 Request per menit per IP (Hanya untuk fitur berat / POST)
    if len(ip_request_tracker[client_ip]) >= 30:
        return JSONResponse(
            status_code=200, 
            content={"error": "Sabar bro! Jangan spam klik, tunggu 1 menit lagi ya. 🛑"}
        )

    # Catat waktu request IP ini
    ip_request_tracker[client_ip].append(current_time)
    
    # Lanjut proses request ke sistem
    response = await call_next(request)
    return response
# ==========================================

# Daftarkan semua routernya
app.include_router(qrcode.router)
app.include_router(image_converter.router)
app.include_router(pdf_merge.router)
app.include_router(pdf_split.router)
app.include_router(pdf_watermark.router)
app.include_router(pdf_protect.router)
app.include_router(pdf_compress.router)
app.include_router(pdf_to_word.router)
app.include_router(remove_bg.router)
app.include_router(image_compressor.router)
app.include_router(pdf_organize.router)
app.include_router(pdf_page_numbers.router)
app.include_router(chatbot.router) 

# VISITOR COUNTER LOGIC
VISITOR_FILE = "visitor.txt"

@app.get("/api/visitor")
async def get_visitor_count():
    count = 0
    if os.path.exists(VISITOR_FILE):
        with open(VISITOR_FILE, "r") as f:
            try: count = int(f.read().strip())
            except: count = 0
    
    count += 1
    
    with open(VISITOR_FILE, "w") as f:
        f.write(str(count))
        
    return {"count": count}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})