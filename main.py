from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os

# Import semua router
from routers import (
    qrcode, image_converter, pdf_merge, pdf_split, 
    pdf_watermark, pdf_protect, pdf_compress, pdf_to_word, 
    remove_bg, image_compressor, pdf_organize, pdf_page_numbers, chatbot
)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

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