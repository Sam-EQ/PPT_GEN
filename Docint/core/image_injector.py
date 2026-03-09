def inject_descriptions(md: str, images, descriptions) -> str:
    for img, desc in zip(images, descriptions):
        marker = f"![]({img['name']})"

        replacement = (
            f"**[Image from page {img['page']}]:** {desc}\n\n{marker}"
        )

        md = md.replace(marker, replacement, 1)

    return md
