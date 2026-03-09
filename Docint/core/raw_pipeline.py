import asyncio
from pathlib import Path
from core.pipeline import _CONVERTER, _CONVERTER_OCR


def _is_likely_scanned(pdf_path: Path) -> bool:
    try:
        from pdfminer.high_level import extract_text
        import fitz  
        text = extract_text(str(pdf_path))
        doc = fitz.open(str(pdf_path))
        num_pages = max(doc.page_count, 1)
        return len(text.strip()) / num_pages < 100
    except Exception:
        return False


def _run_converter(converter, pdf_path: Path):
    result = converter.convert(str(pdf_path))
    return result


async def extract_raw_markdown_with_images(pdf_path: Path) -> str:
    scanned = _is_likely_scanned(pdf_path)
    converter = _CONVERTER_OCR if scanned else _CONVERTER

    if scanned:
        print(f"  [Docint] Detected scanned PDF — using OCR converter")
    else:
        print(f"  [Docint] Detected digital PDF — using standard converter")

    result = await asyncio.to_thread(_run_converter, converter, pdf_path)

    md = result.document.export_to_markdown(
        image_placeholder="",   
        strict_text=False,
    )
    return md.strip()