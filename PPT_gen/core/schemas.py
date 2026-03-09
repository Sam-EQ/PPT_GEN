from pydantic import BaseModel, Field
from typing import List, Optional


class DeckMetadata(BaseModel):
    project_name: str = "PROJECT OVERVIEW"
    project_short_name: str = ""         
    client_name: str = "PROPOSAL ANALYSIS"
    client_logo_path: Optional[str] = None
    doc_type: str = "AE_RFQ"            


class Slide(BaseModel):
    type: str = "bullet"
    title: Optional[str] = None
    bullets: Optional[List[str]] = None
    paragraph: Optional[str] = None

    image_id: Optional[str] = None
    image_path: Optional[str] = None
    image_description: Optional[str] = None

    needs_ai_visual: bool = Field(default=False)
    ai_visual_prompt: Optional[str] = None
    ai_image_path: Optional[str] = None

    notes: Optional[str] = None


class Deck(BaseModel):
    metadata: DeckMetadata
    slides: List[Slide]