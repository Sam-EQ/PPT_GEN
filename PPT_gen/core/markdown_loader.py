from pathlib import Path


def load_markdown(md_path: Path) -> str:
    return md_path.read_text(encoding="utf-8")
    