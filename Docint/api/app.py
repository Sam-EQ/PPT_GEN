import uuid
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File

from config import TEMP_DIR
from core.raw_pipeline import extract_raw_markdown_with_images

app = FastAPI(title="Universal Markdown Extractor")


@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    req_id  = uuid.uuid4().hex
    req_dir = TEMP_DIR / req_id
    req_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = req_dir / file.filename
    with open(pdf_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        markdown = await extract_raw_markdown_with_images(pdf_path)
        return {"markdown": markdown}
    finally:
        shutil.rmtree(req_dir, ignore_errors=True)