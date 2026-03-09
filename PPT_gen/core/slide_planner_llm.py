import json
import os
import re
from openai import AsyncOpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL_SLIDES
from core.schemas import Deck

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

_SHARED_RULES = """
╔══════════════════════════════════════════════════════════════╗
║  BULLET QUALITY — MANDATORY                                  ║
╚══════════════════════════════════════════════════════════════╝

Every bullet MUST:
  • Be a complete sentence of 15–35 words.
  • Contain at least one specific, document-sourced fact: a name,
    date, figure, percentage, form name, URL, phase label, room
    type, or technical requirement.
  • Be written in sharp consulting-brief style — never generic.
  • Never be a statement that could apply to any project of this type.

Target: 6–8 bullets per slide. Hard minimum: 5.
If fewer than 5 strong bullets exist for a topic, MERGE that slide
into its nearest thematic neighbour. Do NOT create thin slides.

╔══════════════════════════════════════════════════════════════╗
║  SLIDE COUNT — MANDATORY                                     ║
╚══════════════════════════════════════════════════════════════╝

Produce every slide in the plan below. Suppress a slide ONLY if
that topic has zero content in the executive summary.
Merging is allowed; omission is not.
The "slides" array MUST contain at least 5 objects. An empty
slides array or a slides array with fewer than 5 items is a
critical failure — never acceptable.

╔══════════════════════════════════════════════════════════════╗
║  VISUAL ASSIGNMENT — STRICT PRIORITY                        ║
╚══════════════════════════════════════════════════════════════╝

For every slide, choose exactly ONE state:

PRIORITY 1 — EXTRACTED ASSET (image_id):
  Assign when the asset description contains any of:
  "map", "aerial", "boundary", "diagram", "chart", "table",
  "timeline", "plan", "section", "logo", "seal", "campus",
  "site", "floor plan", "elevation", "render", "perspective".
  Each asset assigned to ONE slide only — best match wins.

PRIORITY 2 — AI VISUAL (needs_ai_visual: true):
  Only when the slide is conceptual or visionary AND no extracted
  asset fits AND total extracted assets ≤ 5. Max 3 per deck.
  Prompt format: "Professional minimalist [topic] illustration,
  clean white background, slate and cobalt blue palette, geometric
  architectural forms, no text, no people, editorial quality, 16:9."

PRIORITY 3 — TEXT ONLY: needs_ai_visual=false, image_id=null.

╔══════════════════════════════════════════════════════════════╗
║  JSON OUTPUT RULES                                          ║
╚══════════════════════════════════════════════════════════════╝

- Return ONLY the raw JSON object — no markdown fences, no prose.
- needs_ai_visual: boolean true or false (never a string).
- image_id: EXACT asset ID string from the list above, or null.
- title: SHORT, UPPERCASE, max 5 words.
- notes: go/no-go flags or critical caveats only; null otherwise.
"""

_JSON_SCHEMA = """
╔══════════════════════════════════════════════════════════════╗
║  JSON SCHEMA                                                ║
╚══════════════════════════════════════════════════════════════╝
{
  "metadata": {
    "project_name": "Full project title from document",
    "project_short_name": "Short name ≤ 30 chars",
    "client_name": "Exact issuing organization name",
    "client_logo_path": null,
    "doc_type": "<AE_RFQ|DEVELOPER_RFQ|DESIGN_SCOPE>",
    "logo_id": "<exact asset ID or null>"
  },
  "slides": [
    {
      "type": "bullet",
      "title": "UPPERCASE TITLE",
      "bullets": ["Complete sentence with specific fact."],
      "image_id": null,
      "needs_ai_visual": false,
      "ai_visual_prompt": null,
      "notes": null
    }
  ]
}
"""

AE_SYSTEM_PROMPT = """
You are a Senior RFP Strategist at Perkins&Will building a pursuit PowerPoint
for an Architecture & Engineering RFP/RFQ.

Audience: senior partners and pursuit leads who need to quickly assess:
  what is being asked, by whom, key dates, how to win, risks, and
  strategic fit with Perkins&Will.

══ METADATA ════════════════════════════════════════════════════
- project_name: exact full project title from the document
- project_short_name: ≤ 30 chars for slide footers
- client_name: exact issuing organization legal name
- logo_id: asset ID whose description contains "logo", "seal",
  "symbol", or "crest" — or null
- doc_type: "AE_RFQ"

══ SLIDE PLAN ══════════════════════════════════════════════════
Produce ALL slides below. Merge thin slides; never omit entirely.

 1. KEY DATES & MILESTONES
    Every date as a precise bullet. Flag mandatory vs optional events.

 2. CLIENT & PROJECT OVERVIEW
    Client, department, full project title, delivery model, budget,
    owner's representative, location, procurement structure, vision.
    → Assign map / aerial / campus / site asset if available.

 3. SCOPE OF SERVICES — PHASES & DISCIPLINES
    Every phase with label and activities. Every discipline verbatim.
    Delivery date. Group: Phases | Major Disciplines | Other Disciplines.

 4. SCOPE OF SERVICES — SERVICES & SPECIAL CONDITIONS
    All specialist service lines and building services named in scope.
    All live-facility or operational constraints, sequencing rules,
    and special conditions. Merge with slide 3 if combined total ≤ 10 bullets.

 5. DELIVERABLES
    Name specific document types and processes — not categories.

 6. SUBMISSION REQUIREMENTS
    Portal URL verbatim. Required sections by name. Hard copy policy.
    Every form and attachment by exact name. Disqualification triggers.

 7. EVALUATION & SELECTION CRITERIA
    Scoring table with exact point values and sub-breakdowns.
    Highest-weighted criteria flagged. Pass/fail thresholds noted.

 8. COMMERCIAL & CONTRACTUAL TERMS
    Budget verbatim. Fee structure. Contract form name. Insurance type
    and attachment reference. All compliance certifications by name.

 9. RISK, COMPLIANCE & ELIGIBILITY
    Registration requirements. Licensing requirements. Diversity targets
    with exact %. All required forms by name. All legal acknowledgements.
    Team exclusion rules. Disclosure requirements. Go/no-go flags.

10. SCHEDULE & PROCUREMENT PROCESS
    One bullet per step in chronological order through contract award
    and project delivery milestones.

11. STAKEHOLDER ENGAGEMENT & DESIGN VISION
    Every named stakeholder group. Engagement format and cadence.
    Design vision and guiding principles. Referenced plans. Community goals.
    → Assign AI visual if conceptual content warrants it.

12. QUESTIONS, CONTACTS & ADDENDA
    Every contact: Full Name | Title | Email | Phone.
    Question portal, deadline, channel. Addenda process. Blackout rules.

13. ALIGNMENT WITH PERKINS&WILL CORE VALUES
    6 bullets: **[Value]** — [specific fact] — [section ref].
    Values: Design Excellence | Sustainability | Diversity Equity & Inclusion |
    Research | Engagement | Well-Being | Stewardship.
    → Assign AI visual. Go/no-go recommendation in notes field.

""" + _SHARED_RULES + _JSON_SCHEMA

DEVELOPER_SYSTEM_PROMPT = """
You are a Senior RFP Strategist at Perkins&Will building a pursuit PowerPoint
for a Developer / Owner-Operator RFQ.

══ METADATA ════════════════════════════════════════════════════
- project_name: exact full project title
- project_short_name: ≤ 30 chars
- client_name: exact issuing institution name
- logo_id: asset ID with "logo", "seal", "symbol" — or null
- doc_type: "DEVELOPER_RFQ"

══ SLIDE PLAN ══════════════════════════════════════════════════
 1. KEY DATES & MILESTONES
 2. OWNER & PROJECT OVERVIEW — institution, site, vision, structure.
    → Assign map / aerial / site asset if available.
 3. DEVELOPMENT PROGRAM & SCOPE — uses, phasing, areas, sustainability.
 4. DEVELOPER QUALIFICATIONS — experience, financial capacity, team.
 5. SUBMISSION REQUIREMENTS — portal, sections, every mandatory form.
 6. EVALUATION CRITERIA — exact criteria and weights verbatim.
 7. BUSINESS TERMS & TRANSACTION — lease, financing, revenue share.
 8. RISK & KEY CONSIDERATIONS — regulatory, financial, go/no-go flags.
 9. DESIGN & SUSTAINABILITY VISION — design goals, carbon targets.
    → Assign AI visual.
10. QUESTIONS, CONTACTS & ADDENDA — every contact with email.
11. ALIGNMENT WITH PERKINS&WILL CORE VALUES.
    → Assign AI visual. Go/no-go in notes.

""" + _SHARED_RULES + _JSON_SCHEMA

DESIGN_SCOPE_SYSTEM_PROMPT = """
You are a Senior RFP Strategist at Perkins&Will building a pursuit PowerPoint
for an interior design scope of services.

══ METADATA ════════════════════════════════════════════════════
- project_name: exact project name from the document
- project_short_name: ≤ 30 chars
- client_name: exact client / owner name
- logo_id: asset ID with "logo" in description — or null
- doc_type: "DESIGN_SCOPE"

══ SLIDE PLAN ══════════════════════════════════════════════════
 1. PROJECT OVERVIEW
    Client, approval authority, project name and type, brand/operator,
    location, building classification, scale, environments in scope,
    stage gate rule.
    → Assign AI visual or any exterior / interior render asset.

 2. DESIGN AREAS IN SCOPE
    Every space named in the document: top-level zones and specific
    room types from any renders or sample board schedule.
    Note exclusions if stated.

 3. STAGE-BY-STAGE SERVICES
    One bullet block per stage with key activities and sign-off requirement.

 4. DELIVERABLES
    Reproduce quantities, formats, render counts, and material board counts
    verbatim from the document tables.

 5. TECHNICAL & COORDINATION REQUIREMENTS
    File formats, DPI, software, MEP/lighting/ELV coordination, operator
    guidelines, authority approvals, material performance requirements,
    mock-up requirements.

 6. COMMERCIAL & CONTRACT TERMS
    Fee proposal structure. Revision allowances per stage (exact count).
    IP / copyright obligations. Named sub-consultants. Lead consultant
    nomination clause with timeframe. Local sourcing policy if stated.

 7. SUBMISSION & APPROVAL PROCESS
    Sign-off parties. Stage gate rule. Format requirements.
    Presentation requirement at each stage.

 8. ALIGNMENT WITH PERKINS&WILL CORE VALUES
    6 bullets: **[Value]** — [specific fact] — [section ref].
    Values: Design Excellence | Sustainability | Diversity Equity & Inclusion |
    Research | Engagement | Well-Being | Stewardship.
    → Assign AI visual. Go/no-go recommendation in notes.

""" + _SHARED_RULES + _JSON_SCHEMA

_PROMPT_MAP = {
    "AE_RFQ":        AE_SYSTEM_PROMPT,
    "DEVELOPER_RFQ": DEVELOPER_SYSTEM_PROMPT,
    "DESIGN_SCOPE":  DESIGN_SCOPE_SYSTEM_PROMPT,
}


def _infer_short_name(full_name: str) -> str:
    m = re.search(r'\(([^)]+)\)', full_name)
    if m and len(m.group(1)) <= 20:
        return m.group(1)
    if len(full_name) <= 30:
        return full_name
    return full_name[:28].rsplit(' ', 1)[0] + '…'


def _build_asset_context(visual_assets: list) -> str:
    if not visual_assets:
        return "AVAILABLE EXTRACTED ASSETS: (none)\n"
    lines = ["AVAILABLE EXTRACTED ASSETS (use exact IDs):"]
    for a in visual_assets:
        desc = a.get("description", "")[:300].replace('\n', ' ')
        lines.append(
            f"  ID: {a['id']!r}\n"
            f"  Page: {a.get('page')}\n"
            f"  Description: {desc}\n"
        )
    return "\n".join(lines)


FILLER_PHRASES = [
    "not specified", "has not been", "have not been",
    "is not detailed", "are not detailed", "no requirements specified",
    "not provided", "not mentioned", "not outlined", "not detailed",
    "not explicitly", "not included", "not stated", "not yet defined",
    "no information", "unclear from",
]


async def _call_planner(system_prompt: str, user_content: str) -> dict:
    response = await client.chat.completions.create(
        model=OPENAI_MODEL_SLIDES,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_content},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


async def plan_slides(
    summary: str,
    visual_assets: list,
    doc_type: str = "AE_RFQ",
    project_name: str | None = None,
    client_name: str | None = None,
) -> Deck:

    system_prompt = _PROMPT_MAP.get(doc_type, AE_SYSTEM_PROMPT)
    assets_context = _build_asset_context(visual_assets)
    user_content = f"{assets_context}\n\n{'='*60}\nEXECUTIVE SUMMARY:\n{summary}"

    data = await _call_planner(system_prompt, user_content)

    slides_raw = data.get("slides", [])
    if len(slides_raw) < 5:
        print(f"  [Planner] WARNING: only {len(slides_raw)} slides returned — retrying.")
        retry_content = (
            user_content
            + "\n\nCRITICAL: Your previous response returned fewer than 5 slides. "
            "You MUST produce at least 5 slides. The slides array must never be empty."
        )
        data = await _call_planner(system_prompt, retry_content)

    meta = data.get("metadata", {})
    meta["doc_type"] = doc_type

    if project_name:
        meta["project_name"] = project_name
    if client_name:
        meta["client_name"] = client_name

    if not meta.get("project_name") or len(meta.get("project_name", "")) < 5:
        meta["project_name"] = "Project Overview"
    if not meta.get("client_name") or len(meta.get("client_name", "")) < 2:
        meta["client_name"] = "Client"

    full_name = meta.get("project_name", "")
    short = meta.get("project_short_name", "")
    if not short or len(short) > 30:
        meta["project_short_name"] = _infer_short_name(full_name)

    logo_id = meta.pop("logo_id", None)
    if logo_id:
        match = next((a for a in visual_assets if a["id"] == logo_id), None)
        if match:
            meta["client_logo_path"] = os.path.abspath(match["path"])

    used_asset_ids: set[str] = set()
    ai_visual_count = 0

    for slide in data.get("slides", []):
        slide.setdefault("type", "bullet")

        nav = slide.get("needs_ai_visual")
        if isinstance(nav, str):
            slide["needs_ai_visual"] = nav.lower() == "true"

        if slide.get("needs_ai_visual"):
            if ai_visual_count >= 3:
                slide["needs_ai_visual"] = False
            else:
                ai_visual_count += 1

        img_id = slide.get("image_id")
        if img_id:
            if img_id in used_asset_ids:
                slide["image_id"] = None
            else:
                match = next((a for a in visual_assets if a["id"] == img_id), None)
                if match:
                    slide["image_path"] = os.path.abspath(match["path"])
                    slide["image_description"] = match.get("description", "")
                    used_asset_ids.add(img_id)
                else:
                    slide["image_id"] = None

        if slide.get("needs_ai_visual") and not slide.get("ai_visual_prompt"):
            slide["needs_ai_visual"] = False

        bullets = slide.get("bullets") or []
        cleaned = [
            b for b in bullets
            if not any(p in b.lower() for p in FILLER_PHRASES)
        ]
        slide["bullets"] = cleaned if len(cleaned) >= 2 else bullets

    data["slides"] = [
        s for s in data.get("slides", [])
        if (s.get("bullets") and len(s["bullets"]) > 0)
        or s.get("image_id")
        or s.get("needs_ai_visual")
        or s.get("paragraph")
    ]

    data["metadata"] = meta
    return Deck(**data)