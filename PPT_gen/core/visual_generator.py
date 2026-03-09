import os
import uuid
import base64
import httpx
from pathlib import Path
from openai import AsyncOpenAI
from config import OPENAI_API_KEY

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

async def generate_missing_visuals(deck, run_dir: Path):
    gen_dir = run_dir / "ai_visuals"
    gen_dir.mkdir(parents=True, exist_ok=True)

    for slide in deck.slides:
        if slide.needs_ai_visual and slide.ai_visual_prompt:
            print(f"Generating AI visual for: {slide.title}")
            try:
                response = await client.images.generate(
                    model="dall-e-3",
                    prompt=slide.ai_visual_prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                )
                image_url = response.data[0].url
                
                img_path = gen_dir / f"{uuid.uuid4().hex[:8]}.png"
                async with httpx.AsyncClient() as h_client:
                    img_data = await h_client.get(image_url)
                    img_path.write_bytes(img_data.content)
                
                slide.ai_image_path = str(img_path.absolute())
            except Exception as e:
                print(f"AI Generation failed: {e}")