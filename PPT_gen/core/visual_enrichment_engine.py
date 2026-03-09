def enrich_slides(deck):
    for slide in deck.slides:
        if not slide.visual_hint:
            if "timeline" in slide.title.lower():
                slide.visual_hint = "Timeline diagram"
            elif "budget" in slide.title.lower():
                slide.visual_hint = "Cost breakdown chart"
            elif "strategy" in slide.title.lower():
                slide.visual_hint = "Conceptual framework graphic"
            else:
                slide.visual_hint = "Minimal supporting visual"

    return deck
    