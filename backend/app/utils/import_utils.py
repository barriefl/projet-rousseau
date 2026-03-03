import math
import re
import unicodedata


def normalize_text(text: str | None) -> str:
    """Met en minuscules, retire les accents et les espaces superflus."""
    if not text:
        return ""

    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")
    text = text.lower()
    text = text.replace("-", " ")
    text = re.sub(r"\s+", " ", text).strip()

    return text


def sort_semicolon_list(text: str | None) -> str | None:
    """Trie une chaîne séparée par des points-virgules par ordre alphabétique."""
    if not text:
        return None

    items = [item.strip() for item in text.split(";") if item.strip()]
    items.sort()
    return ";".join(items) if items else None


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calcule la distance de Levenshtein entre deux chaînes."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def is_fuzzy_match(str1: str, str2: str) -> bool:
    """
    Vérifie si deux chaînes correspondent selon la règle :
    1 faute autorisée par tranche de 4 caractères (basé sur la chaîne la plus longue).
    """
    norm1 = normalize_text(str1)
    norm2 = normalize_text(str2)

    if norm1 == norm2:
        return True

    max_len = max(len(norm1), len(norm2))
    allowed_mistakes = max_len // 4

    if allowed_mistakes == 0:
        return False

    dist = levenshtein_distance(norm1, norm2)
    return dist <= allowed_mistakes


def clean_float(value: str | int | float | None) -> float | None:
    """Convertit une chaîne (ex: '15,5' ou '15.5%') en float propre."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value) if not math.isnan(value) else None

    val_str = str(value).strip().replace(",", ".").replace("%", "").replace(" ", "")
    try:
        return float(val_str)
    except ValueError:
        return None


def find_col_by_keyword(
    headers: list[str], keywords: str | list[str], exclude: list[str] = None
) -> str | None:
    """
    Trouve le nom exact d'une colonne.
    L'ordre des keywords définit la priorité.
    """
    if isinstance(keywords, str):
        keywords = [keywords]
    if exclude is None:
        exclude = []

    for kw in keywords:
        kw_lower = kw.lower()
        for header in headers:
            header_lower = header.lower()

            if any(ex.lower() in header_lower for ex in exclude):
                continue

            if kw_lower in header_lower:
                return header

    return None
