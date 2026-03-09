import asyncio
import sys
import uuid
import json
from pathlib import Path

from core.markdown_loader import load_markdown
from core.markdown_cleaner import clean_markdown
from core.executive_summary_llm import generate_executive_summary, _classify_document
from core.slide_planner_llm import plan_slides
from core.visual_generator import generate_missing_visuals
from renderers.pptx_renderer import render_pptx
from config import DEBUG_DIR


def deck_to_markdown(deck):
    md = []

    md.append(f"# {deck.metadata.project_name}")
    md.append("")

    for i, slide in enumerate(deck.slides, 1):
        md.append(f"## Slide {i}: {slide.title}")
        md.append("")

        if slide.bullets:
            for b in slide.bullets:
                md.append(f"- {b}")

        if slide.image_path:
            md.append(f"\nImage: {slide.image_path}")

        if slide.ai_visual_prompt:
            md.append(f"\nAI Visual Prompt: {slide.ai_visual_prompt}")

        md.append("")
        md.append("---")
        md.append("")

    return "\n".join(md)


async def debug_pipeline(md_path: Path, registry_path: Path):

    run_id = uuid.uuid4().hex[:8]
    run_dir = DEBUG_DIR / f"debug_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n--- DEBUG RUN: {run_id} ---\n")

    raw_md = load_markdown(md_path)

    (run_dir / "raw_markdown.md").write_text(raw_md)

    print("Cleaning markdown...")
    cleaned = clean_markdown(raw_md)

    cleaned_path = run_dir / "cleaned_markdown.md"
    cleaned_path.write_text(cleaned)

    print(f"Saved → {cleaned_path}")

    visual_assets = []

    if registry_path.exists():
        registry = json.loads(registry_path.read_text())
        visual_assets = registry.get("images", [])

    registry_copy = run_dir / "visual_assets.json"
    registry_copy.write_text(json.dumps({"images": visual_assets}, indent=2))

    print(f"Visual assets: {len(visual_assets)}")

    print("Classifying document type...")
    doc_type = await _classify_document(cleaned)

    print(f"Document type: {doc_type}")

    (run_dir / "doc_type.txt").write_text(doc_type)

    print("Generating executive summary...")

    summary = await generate_executive_summary(cleaned)

    summary_path = run_dir / "executive_summary.md"
    summary_path.write_text(summary)

    print(f"Saved → {summary_path}")

    print("Planning slides...")

    deck = await plan_slides(summary, visual_assets, doc_type=doc_type)

    print(f"Slides planned: {len(deck.slides)}")

    slide_plan_json = run_dir / "slide_plan.json"
    slide_plan_json.write_text(json.dumps(deck.model_dump(), indent=2))

    print(f"Saved → {slide_plan_json}")

    planner_md = deck_to_markdown(deck)

    slide_plan_md = run_dir / "slide_plan.md"
    slide_plan_md.write_text(planner_md)

    print(f"Saved → {slide_plan_md}")

    print("Generating AI visuals if required...")
    await generate_missing_visuals(deck, run_dir)

    out_path = run_dir / f"RFP_Analysis_{run_id}.pptx"

    render_pptx(deck, out_path)

    print("\nSUCCESS")
    print(f"PPTX → {out_path.absolute()}")
    print(f"Debug artifacts → {run_dir.absolute()}\n")


if __name__ == "__main__":

    if len(sys.argv) != 3:
        print("\nUsage:")
        print("python debug.py <markdown_path> <visual_assets_json>\n")
        sys.exit(1)

    md_path = Path(sys.argv[1])
    registry_path = Path(sys.argv[2])

    asyncio.run(debug_pipeline(md_path, registry_path))