import asyncio
import json
import uuid
from pathlib import Path

from core.markdown_loader import load_markdown
from core.markdown_cleaner import clean_markdown, extract_document_header
from core.executive_summary_llm import generate_executive_summary, _classify_document
from core.slide_planner_llm import plan_slides
from core.visual_generator import generate_missing_visuals
from renderers.pptx_renderer import render_pptx
from config import DEBUG_DIR


async def build_universal_deck(md_path: Path, registry_path: Path) -> str:
    run_id  = uuid.uuid4().hex[:8]
    run_dir = DEBUG_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"  Build ID: {run_id}")

    raw_md  = load_markdown(md_path)
    cleaned = clean_markdown(raw_md)

    (run_dir / "raw_markdown.md").write_text(raw_md, encoding="utf-8")
    (run_dir / "cleaned_markdown.md").write_text(cleaned, encoding="utf-8")

    client_hint, project_hint = extract_document_header(cleaned)
    print(f"  Header hints — Client: {client_hint!r}  Project: {project_hint!r}")

    print("\n  Classifying document...")
    doc_type = await _classify_document(cleaned)
    print(f"  Document type: {doc_type}")
    (run_dir / "doc_type.txt").write_text(doc_type, encoding="utf-8")

    print("\n  Generating executive summary...")
    summary = await generate_executive_summary(cleaned, doc_type=doc_type)
    (run_dir / "executive_summary.md").write_text(summary, encoding="utf-8")
    print(f"  Summary: {len(summary)} chars")

    visual_assets = []
    if registry_path.exists():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        visual_assets = registry.get("images", [])
    print(f"\n  Visual assets: {len(visual_assets)}")

    print("\n  Planning slides...")
    deck = await plan_slides(
        summary=summary,
        visual_assets=visual_assets,
        doc_type=doc_type,
        project_name=None,  
        client_name=None,
    )

    if not deck.metadata.project_name or len(deck.metadata.project_name) < 5:
        deck.metadata.project_name = project_hint or "RFP Analysis"
    if not deck.metadata.client_name or len(deck.metadata.client_name) < 3:
        deck.metadata.client_name = client_hint or "Client"

    print(f"  Slides planned: {len(deck.slides)}")
    print(f"  Project: {deck.metadata.project_name}")
    print(f"  Client:  {deck.metadata.client_name}")

    import json as _json
    (run_dir / "slide_plan.json").write_text(
        _json.dumps(deck.model_dump(), indent=2), encoding="utf-8")

    print("\n  Generating AI visuals...")
    await generate_missing_visuals(deck, run_dir)

    out_path = run_dir / f"RFP_Analysis_{run_id}.pptx"
    render_pptx(deck, out_path)

    print(f"\n  ✓ SUCCESS")
    print(f"  PPTX   → {out_path.absolute()}")
    print(f"  Run dir → {run_dir.absolute()}\n")

    return str(out_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python pipeline.py <markdown_path> <visual_assets_json>")
        sys.exit(1)
    asyncio.run(build_universal_deck(Path(sys.argv[1]), Path(sys.argv[2])))