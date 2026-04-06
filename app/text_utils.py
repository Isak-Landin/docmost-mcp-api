import re


def reformat_text(text: str) -> str:
    """
    Normalize raw text_content from Docmost storage.

    Docmost stores page text with repeated newline sequences and repeated '+'
    characters that are storage artefacts rather than meaningful content.

    Transformations applied:
    - Collapse runs of 3+ consecutive '+' characters down to a single '+'
    - Collapse runs of 2+ consecutive newlines down to a single newline
    - Strip leading/trailing whitespace from the result
    """
    if not text:
        return text
    text = re.sub(r'\+{3,}', '+', text)
    text = re.sub(r'\n{2,}', '\n', text)
    return text.strip()
