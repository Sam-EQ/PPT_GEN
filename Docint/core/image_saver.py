from pathlib import Path
import uuid


def save_docling_image(pil_image, output_dir: Path, page: int | None, idx: int = 0) -> Path:

    output_dir.mkdir(parents=True, exist_ok=True)

    page_str = f"page_{page}_" if page is not None else "page_unknown_"
    filename = f"{page_str}fig{idx:03d}_{uuid.uuid4().hex[:6]}.jpg"
    path = output_dir / filename

    if getattr(pil_image, "mode", "RGB") in ("RGBA", "LA", "P"):
        pil_image = pil_image.convert("RGB")
    elif getattr(pil_image, "mode", "RGB") != "RGB":
        pil_image = pil_image.convert("RGB")

    pil_image.save(path, format="JPEG", quality=92)
    return path