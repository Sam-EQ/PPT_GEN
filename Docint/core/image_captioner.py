import asyncio
import base64
import io
from openai import AsyncOpenAI
from config import OPENAI_API_KEY

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
You are a precise document-vision analysis system.

Your task is to describe images extracted from documents.

If the figure is timeline, schedule, org chart, flowchart, or any other type of diagram, you should describe the diagram without ommiting similar patterns and also describe its structure, labels, relationships, key data points, and meaning.


STRICT RULES:
- Describe ONLY what is visible
- Do NOT summarize
- Do NOT generalize
- Do NOT infer missing information
- Do NOT omit repeated elements
- Preserve numbers, labels, and terminology exactly
- If text is unreadable → write [illegible]

REQUIREMENTS:
- Provide a detailed descriptive explanation
- Describe structure and layout
- Include all visible textual elements
- Neutral technical tone
"""

MAX_CONCURRENT = 15
_semaphore = asyncio.Semaphore(MAX_CONCURRENT)


def _image_to_data_url(image) -> str:

    if isinstance(image, (str, bytes)):
        with open(image, "rb") as f:
            raw = f.read()
        mime = "image/jpeg"

    elif hasattr(image, "save"):  # PIL Image
        buf = io.BytesIO()
        image.save(buf, format="JPEG")
        raw = buf.getvalue()
        mime = "image/jpeg"

    elif hasattr(image, "image"):  # Marker Image object
        buf = io.BytesIO()
        image.image.save(buf, format="JPEG")
        raw = buf.getvalue()
        mime = "image/jpeg"

    else:
        raise TypeError(f"Unsupported image type: {type(image)}")

    encoded = base64.b64encode(raw).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


async def describe_image(image_obj) -> str:
    async with _semaphore:
        image_data_url = _image_to_data_url(image_obj)

        response = await client.responses.create(
            model="gpt-4o-mini",
            temperature=0,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Provide a complete, detailed description of this image."
                        },
                        {
                            "type": "input_image",
                            "image_url": image_data_url,
                        },
                    ],
                },
            ],
        )

        return response.output_text.strip()


async def describe_images_parallel(images):
    tasks = [describe_image(img["image"]) for img in images]
    return await asyncio.gather(*tasks)
