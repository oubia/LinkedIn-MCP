import re
import unicodedata


def slugify(value: str, *, max_length: int = 200) -> str:
    normalized = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    cleaned = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip("-")
    return cleaned or "job"
