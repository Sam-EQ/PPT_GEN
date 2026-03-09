import asyncio
import sys
import time
import json
from pathlib import Path

from config import TEMP_DIR
from core.pipeline import _CONVERTER
from core.image_extractor import extract_images
from core.image_captioner import describe_images_parallel
from core.image_injector import inject_descriptions


async def debug_pipeline(pdf: Path):
    start_total = time.perf_counter()

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    out = TEMP_DIR / "debug"
    out.mkdir(parents=True, exist_ok=True)
    image_dir = out / "images"
    image_dir.mkdir(parents=True, exist_ok=True)

    print(f"PDF: {pdf.name}")
    t0 = time.perf_counter()

    result = await asyncio.to_thread(_CONVERTER.convert, str(pdf))
    md = result.document.export_to_markdown(
        image_placeholder="",
        strict_text=False,
    ).strip()

    print(f"Docling extraction: {time.perf_counter() - t0:.2f}s")

    t0 = time.perf_counter()

    images = extract_images(result, image_dir)
    print(f"Images detected: {len(images)}")
    print(f"Image extraction + saving: {time.perf_counter() - t0:.2f}s")
    t0 = time.perf_counter()

    descriptions = await describe_images_parallel(images)
    print(f"Image captioning: {time.perf_counter() - t0:.2f}s")

    t0 = time.perf_counter()

    final_md = inject_descriptions(md, images, descriptions)
    md_path = out / "final_with_images.md"
    md_path.write_text(final_md, encoding="utf-8")
    print(f"Injection + write: {time.perf_counter() - t0:.2f}s")

    registry = {"images": []}
    for img, desc in zip(images, descriptions):
        registry["images"].append({
            "id":          img["id"],
            "source":      "extracted",
            "page":        img["page"],
            "path":        img["path"],
            "description": desc,
        })

    registry_path = out / "visual_assets.json"
    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")

    total = time.perf_counter() - start_total
    print("\nDone")
    print(f"Markdown  → {md_path}")
    print(f"Images    → {image_dir}")
    print(f"Registry  → {registry_path}")
    print(f"⏱ TOTAL TIME: {total:.2f}s")


if __name__ == "__main__":
    asyncio.run(debug_pipeline(Path(sys.argv[1])))