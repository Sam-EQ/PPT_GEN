import re


def extract_document_header(md: str):
    lines = md.splitlines()[:60]

    headings = []
    for line in lines:
        clean = re.sub(r'[#*_]', '', line).strip()
        if 5 < len(clean) < 120:
            headings.append(clean)

    client  = None
    project = None

    client_keywords = [
        "university", "college", "city of", "county", "authority",
        "department", "institute", "board of", "commission"
    ]
    for h in headings:
        l = h.lower()
        if any(kw in l for kw in client_keywords) and not client:
            client = h
            break

    project_keywords = [
        "master plan", "expansion", "convention center", "hub", "facility",
        "campus", "library", "services", "design", "project", "rfp", "rfq"
    ]
    for h in headings:
        l = h.lower()
        if any(kw in l for kw in project_keywords) and h != client and not project:
            project = h
            break

    return client, project



def _collapse_image_blocks(md: str) -> str:
    pattern = re.compile(
        r'\*\*\[Image from page (\d+)\]\:\*\*\s*(.*?)(?=!\[\]|\Z)',
        re.DOTALL
    )

    def shorten(match):
        page = match.group(1)
        raw  = match.group(2)
        desc = re.sub(r'#+\s+', '', raw)
        desc = re.sub(r'\*\*(.+?)\*\*', r'\1', desc)
        desc = re.sub(r'^\s*[-•]\s*', '', desc, flags=re.MULTILINE)
        desc = re.sub(r'\n+', ' ', desc).strip()
        if len(desc) > 100:
            desc = desc[:97].rsplit(' ', 1)[0] + '...'
        return f"[Figure, page {page}: {desc}]\n"

    return pattern.sub(shorten, md)


def _strip_page_separators(md: str) -> str:
    return re.sub(r'^\{\d+\}-{10,}', '', md, flags=re.MULTILINE)


def _strip_ocr_noise(md: str) -> str:
    md = re.sub(r'-{20,}', '', md)
    md = re.sub(r'Page\s+\d+\s+of\s+\d+', '', md, flags=re.IGNORECASE)
    md = re.sub(r'Appendix\s+\w+\s+Page\s+\d+\s+of\s+\d+', '', md, flags=re.IGNORECASE)
    md = re.sub(r'^\s*Page\s+\d+\s*$', '', md, flags=re.MULTILINE | re.IGNORECASE)
    return md


def clean_markdown(md: str) -> str:
    md = _collapse_image_blocks(md)
    md = _strip_page_separators(md)
    md = _strip_ocr_noise(md)

    lines = md.splitlines()
    cleaned = []
    prev_blank = False

    for line in lines:
        if re.match(r'^\s*-{15,}\s*$', line):
            continue

        stripped = line.rstrip()

        if '|' not in stripped:  
            stripped = re.sub(r'  +', ' ', stripped)

        is_blank = not stripped.strip()

        if is_blank:
            if not prev_blank:
                cleaned.append('')
            prev_blank = True
            continue

        prev_blank = False

        cleaned.append(stripped)

    return '\n'.join(cleaned).strip()