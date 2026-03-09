from typing import List, Dict
from pathlib import Path

from core.image_saver import save_docling_image
MIN_WIDTH_PX  = 100
MIN_HEIGHT_PX = 80

MAX_ASPECT_RATIO = 20.0


def _resolve_pil(pic, doc):
    img_ref = getattr(pic, "image", None)

    if img_ref is not None:
        pil = getattr(img_ref, "pil_image", None)
        if pil is not None:
            return pil

    if img_ref is not None and hasattr(img_ref, "mode"):
        return img_ref

    try:
        pil = pic.get_image(doc)
        if pil is not None:
            return pil
    except Exception:
        pass

    return None


def _is_decorative(pil_img) -> bool:
    w, h = pil_img.size

    if w < MIN_WIDTH_PX or h < MIN_HEIGHT_PX:
        return True

    aspect = w / h if h > 0 else float("inf")
    if aspect > MAX_ASPECT_RATIO:
        return True

    return False


def extract_images(conversion_result, image_output_dir: Path) -> List[Dict]:
    images: List[Dict] = []
    doc = conversion_result.document

    if not doc.pictures:
        return images

    skipped = 0
    for idx, pic in enumerate(doc.pictures):
        page = None
        if pic.prov:
            page = pic.prov[0].page_no

        pil_img = _resolve_pil(pic, doc)
        if pil_img is None:
            print(f"  [Warning] Could not resolve image for picture {idx} (page {page}), skipping.")
            skipped += 1
            continue

        if _is_decorative(pil_img):
            print(f"  [Filter] Skipping decorative image: picture {idx} (page {page}) — {pil_img.size}")
            skipped += 1
            continue

        img_id = f"picture_{idx}_page_{page}"
        saved_path = save_docling_image(pil_img, image_output_dir, page, idx)

        images.append({
            "id":    img_id,
            "name":  img_id,
            "image": pil_img,
            "page":  page,
            "path":  str(saved_path),
        })

    if skipped:
        print(f"  [Filter] {skipped} decorative/unresolvable image(s) skipped.")

    return images