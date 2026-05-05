from __future__ import annotations

import re


def clean_extracted_text(text: str) -> str:
    cleaned = text or ""
    replacements = {
        "\ufeff": "",
        "\u200b": "",
        "\u200c": "",
        "\u200d": "",
        "\xa0": " ",
        "Â·": "•",
        "â€¢": "•",
        "â€“": "-",
        "â€”": "-",
        "â€˜": "'",
        "â€™": "'",
        "â€œ": '"',
        "â€": '"',
    }
    for source, target in replacements.items():
        cleaned = cleaned.replace(source, target)

    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()
