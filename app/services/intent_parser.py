"""Intent parsing service with cached fallback for demo reliability."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from app.domain.enums import InputType, IntentCategory, ParserMode, SupportedLanguage
from app.domain.models import ParsedIntent


# --- Cached demo examples ---

_CACHED_DEMO_INTENTS: dict[str, ParsedIntent] = {
    "https://example.com/headphones-demo": ParsedIntent(
        input_type=InputType.url,
        source_text="https://example.com/headphones-demo",
        normalized_title="wireless headphones",
        localized_title="Беспроводные наушники",
        language=SupportedLanguage.ru,
        category=IntentCategory.electronics,
        specs={"source_url_domain": "example.com"},
        estimated_unit_price_kzt=None,
        budget_min_kzt=None,
        budget_max_kzt=15000,
        confidence=0.85,
        parser_mode=ParserMode.cache_fallback,
        explanation="Cached demo example for headphones URL.",
    ),
    "Хочу беспроводные наушники до 15000 тенге": ParsedIntent(
        input_type=InputType.text,
        source_text="Хочу беспроводные наушники до 15000 тенге",
        normalized_title="wireless headphones",
        localized_title="Беспроводные наушники",
        language=SupportedLanguage.ru,
        category=IntentCategory.electronics,
        specs={"wireless": True},
        estimated_unit_price_kzt=None,
        budget_min_kzt=None,
        budget_max_kzt=15000,
        confidence=0.85,
        parser_mode=ParserMode.cache_fallback,
        explanation="Cached demo example for Russian headphones request.",
    ),
    "Маған үйге ауа ылғалдатқыш керек": ParsedIntent(
        input_type=InputType.text,
        source_text="Маған үйге ауа ылғалдатқыш керек",
        normalized_title="home humidifier",
        localized_title="Ауа ылғалдатқыш",
        language=SupportedLanguage.kk,
        category=IntentCategory.home,
        specs={},
        estimated_unit_price_kzt=None,
        budget_min_kzt=None,
        budget_max_kzt=None,
        confidence=0.85,
        parser_mode=ParserMode.cache_fallback,
        explanation="Cached demo example for Kazakh humidifier request.",
    ),
    "I want a cheap portable projector": ParsedIntent(
        input_type=InputType.text,
        source_text="I want a cheap portable projector",
        normalized_title="portable projector",
        localized_title="Portable Projector",
        language=SupportedLanguage.en,
        category=IntentCategory.electronics,
        specs={},
        estimated_unit_price_kzt=None,
        budget_min_kzt=None,
        budget_max_kzt=None,
        confidence=0.65,
        parser_mode=ParserMode.cache_fallback,
        explanation="Cached demo example for English projector request.",
    ),
}


def _detect_language(text: str, user_language: str | None = None) -> SupportedLanguage:
    """Detect language from text or use provided user language."""
    if user_language in ("kk", "ru", "en"):
        return SupportedLanguage(user_language)

    # Check for Kazakh-specific Cyrillic letters
    kazakh_letters = "әғқңөұүһіӘҒҚҢӨҰҮҺІ"
    has_kazakh = any(c in text for c in kazakh_letters)

    # Check if mostly Cyrillic (Unicode range U+0400 to U+04FF)
    is_cyrillic = any(0x0400 <= ord(c) <= 0x04FF for c in text)

    if has_kazakh:
        return SupportedLanguage.kk
    if is_cyrillic:
        return SupportedLanguage.ru

    # Check for mostly Latin letters
    if any(c.isalpha() and ord(c) < 128 for c in text):
        return SupportedLanguage.en

    return SupportedLanguage.unknown


def _detect_input_type(text: str) -> InputType:
    """Detect if input is URL or text."""
    stripped = text.strip()
    if stripped.startswith("http://") or stripped.startswith("https://"):
        return InputType.url
    return InputType.text


def _categorize_intent(text: str) -> IntentCategory:
    """Categorize intent using deterministic keyword rules."""
    text_lower = text.lower()

    # Electronics keywords
    electronics_keywords = [
        "headphones", "earphones", "airpods", "phone", "smartphone", "laptop",
        "projector", "camera",
        "наушники", "құлаққап", "телефон", "смартфон", "ноутбук", "проектор", "камера",
    ]
    if any(kw in text_lower for kw in electronics_keywords):
        return IntentCategory.electronics

    # Home keywords
    home_keywords = [
        "humidifier", "kettle", "kitchen", "cookware", "dishes",
        "увлажнитель", "посуда", "чайник", "кухня",
        "ауа ылғалдатқыш", "ыдыс", "шәйнек",
    ]
    if any(kw in text_lower for kw in home_keywords):
        return IntentCategory.home

    # Fashion keywords
    fashion_keywords = [
        "jacket", "shoes", "sneakers", "hoodie", "jeans",
        "куртка", "кроссовки", "обувь", "джинсы",
        "күрте", "аяқ киім",
    ]
    if any(kw in text_lower for kw in fashion_keywords):
        return IntentCategory.fashion

    # Beauty keywords
    beauty_keywords = [
        "cosmetics", "skincare", "cream", "perfume",
        "косметика", "крем", "парфюм",
        "косметика", "крем", "иіссу",
    ]
    if any(kw in text_lower for kw in beauty_keywords):
        return IntentCategory.beauty

    # Sports keywords
    sports_keywords = [
        "basketball", "ball", "dumbbells", "fitness", "bike",
        "баскетбол", "мяч", "гантели", "велосипед",
        "доп", "гантель", "велосипед",
    ]
    if any(kw in text_lower for kw in sports_keywords):
        return IntentCategory.sports

    # Kids keywords
    kids_keywords = [
        "toy", "lego", "children", "kids",
        "игрушка", "детский", "дети",
        "ойыншық", "балалар",
    ]
    if any(kw in text_lower for kw in kids_keywords):
        return IntentCategory.kids

    # Auto keywords
    auto_keywords = [
        "car", "dashcam", "vacuum", "accessory",
        "авто", "машина", "видеорегистратор", "автопылесос",
        "көлік", "бейнетіркегіш",
    ]
    if any(kw in text_lower for kw in auto_keywords):
        return IntentCategory.auto

    # Books keywords
    books_keywords = [
        "book", "textbook", "novel",
        "книга", "учебник",
        "кітап", "оқулық",
    ]
    if any(kw in text_lower for kw in books_keywords):
        return IntentCategory.books

    return IntentCategory.other


def _normalize_title(category: IntentCategory, text: str, language: SupportedLanguage) -> str:
    """Normalize title based on category and input."""
    text_lower = text.lower()

    # Map to standard English titles
    if category == IntentCategory.electronics:
        if any(kw in text_lower for kw in ["headphones", "наушники", "құлаққап", "earphones", "airpods"]):
            return "wireless headphones"
        if any(kw in text_lower for kw in ["projector", "проектор"]):
            return "portable projector"
        if any(kw in text_lower for kw in ["phone", "телефон", "смартфон", "smartphone"]):
            return "smartphone"
        if any(kw in text_lower for kw in ["laptop", "ноутбук"]):
            return "laptop"
        if any(kw in text_lower for kw in ["camera", "камера"]):
            return "camera"

    if category == IntentCategory.home:
        if any(kw in text_lower for kw in ["humidifier", "увлажнитель", "ауа ылғалдатқыш"]):
            return "home humidifier"
        if any(kw in text_lower for kw in ["kettle", "чайник", "шәйнек"]):
            return "electric kettle"
        if any(kw in text_lower for kw in ["kitchen", "кухня"]):
            return "kitchen cookware"

    if category == IntentCategory.fashion:
        if any(kw in text_lower for kw in ["jacket", "куртка", "күрте"]):
            return "fashion jacket"
        if "basketball" in text_lower or "баскетбол" in text_lower:
            if any(kw in text_lower for kw in ["shoes", "кроссовки", "аяқ киім", "sneakers"]):
                return "basketball shoes"
        if any(kw in text_lower for kw in ["shoes", "кроссовки", "аяқ киім", "sneakers", "обувь"]):
            return "shoes"
        if any(kw in text_lower for kw in ["jeans", "джинсы"]):
            return "jeans"

    if category == IntentCategory.beauty:
        if any(kw in text_lower for kw in ["cosmetics", "косметика"]):
            return "cosmetics set"
        if any(kw in text_lower for kw in ["cream", "крем"]):
            return "face cream"
        if any(kw in text_lower for kw in ["perfume", "парфюм", "иіссу"]):
            return "perfume"

    if category == IntentCategory.sports:
        if any(kw in text_lower for kw in ["basketball", "баскетбол", "доп"]):
            return "basketball"
        if any(kw in text_lower for kw in ["dumbbells", "гантели", "гантель"]):
            return "dumbbells"
        if any(kw in text_lower for kw in ["bike", "велосипед"]):
            return "bicycle"

    if category == IntentCategory.kids:
        if any(kw in text_lower for kw in ["toy", "игрушка", "ойыншық", "lego"]):
            return "kids toy"

    if category == IntentCategory.auto:
        if any(kw in text_lower for kw in ["dashcam", "видеорегистратор", "бейнетіркегіш"]):
            return "car dashcam"
        if any(kw in text_lower for kw in ["car", "авто", "машина", "көлік"]):
            return "car accessory"

    if category == IntentCategory.books:
        if any(kw in text_lower for kw in ["book", "книга", "кітап", "учебник", "оқулық"]):
            return "book"

    # Fallback: clean and truncate input text
    cleaned = re.sub(r"[^\w\s]", "", text).strip()
    return cleaned[:80] if len(cleaned) > 80 else cleaned


def _localized_title(category: IntentCategory, text: str, language: SupportedLanguage) -> str:
    """Generate localized title based on input language."""
    text_lower = text.lower()

    if language == SupportedLanguage.ru:
        # Russian localized titles
        if category == IntentCategory.electronics:
            if any(kw in text_lower for kw in ["headphones", "наушники", "құлаққап"]):
                return "Беспроводные наушники"
            if any(kw in text_lower for kw in ["projector", "проектор"]):
                return "Портативный проектор"
            if any(kw in text_lower for kw in ["phone", "телефон", "смартфон"]):
                return "Смартфон"
            if any(kw in text_lower for kw in ["laptop", "ноутбук"]):
                return "Ноутбук"
            if any(kw in text_lower for kw in ["camera", "камера"]):
                return "Камера"

        if category == IntentCategory.home:
            if any(kw in text_lower for kw in ["humidifier", "увлажнитель", "ауа ылғалдатқыш"]):
                return "Увлажнитель воздуха"
            if any(kw in text_lower for kw in ["kettle", "чайник", "шәйнек"]):
                return "Электрический чайник"

        if category == IntentCategory.fashion:
            if any(kw in text_lower for kw in ["jacket", "куртка", "күрте"]):
                return "Модная куртка"
            if any(kw in text_lower for kw in ["shoes", "кроссовки", "обувь"]):
                return "Обувь"

        if category == IntentCategory.kids:
            if any(kw in text_lower for kw in ["toy", "игрушка", "ойыншық"]):
                return "Детская игрушка"

        if category == IntentCategory.auto:
            if any(kw in text_lower for kw in ["dashcam", "видеорегистратор"]):
                return "Автомобильный видеорегистратор"

        if category == IntentCategory.books:
            if any(kw in text_lower for kw in ["book", "книга", "кітап"]):
                return "Книга"

    elif language == SupportedLanguage.kk:
        # Kazakh localized titles
        if category == IntentCategory.electronics:
            if any(kw in text_lower for kw in ["headphones", "наушники", "құлаққап"]):
                return "Сымсыз құлаққап"
            if any(kw in text_lower for kw in ["projector", "проектор"]):
                return "Портативті проектор"

        if category == IntentCategory.home:
            if any(kw in text_lower for kw in ["humidifier", "увлажнитель", "ауа ылғалдатқыш"]):
                return "Ауа ылғалдатқыш"
            if any(kw in text_lower for kw in ["kettle", "чайник", "шәйнек"]):
                return "Электр шәйнек"

        if category == IntentCategory.fashion:
            if any(kw in text_lower for kw in ["jacket", "куртка", "күрте"]):
                return "Сән күрте"

        if category == IntentCategory.kids:
            if any(kw in text_lower for kw in ["toy", "игрушка", "ойыншық"]):
                return "Балалар ойыншығы"

        if category == IntentCategory.auto:
            if any(kw in text_lower for kw in ["dashcam", "видеорегистратор", "бейнетіркегіш"]):
                return "Көлік бейнетіркегіш"

        if category == IntentCategory.books:
            if any(kw in text_lower for kw in ["book", "книга", "кітап"]):
                return "Кітап"

    # English or unknown: title-case the normalized title
    normalized = _normalize_title(category, text, language)
    return normalized.title()


def _extract_budget(text: str) -> tuple[int | None, int | None, int | None]:
    """Extract budget information from text.

    Returns:
        (estimated_unit_price_kzt, budget_min_kzt, budget_max_kzt)
    """
    text_lower = text.lower()

    # Patterns for price extraction
    # Match numbers with optional spaces/thousand separators
    price_pattern = r"(\d[\d\s]*)\s*(?:тенге|теңге|тг|₸|kzt|tenge)?\b"

    # Check for "до X" or "under X" patterns (budget max)
    budget_max_patterns = [
        r"до\s+(\d[\d\s]*)",
        r"under\s+(\d[\d\s]*(?:k|\s*k)?)",
    ]

    for pattern in budget_max_patterns:
        match = re.search(pattern, text_lower)
        if match:
            value_str = match.group(1).replace(" ", "").replace("k", "000").replace("K", "000")
            try:
                budget_max = int(value_str)
                return (None, None, budget_max)
            except ValueError:
                pass

    # Check for single price mention (estimated unit price)
    matches = re.findall(price_pattern, text_lower)
    if matches:
        # Take the first valid price found
        for match in matches:
            value_str = match.replace(" ", "")
            try:
                price = int(value_str)
                if price > 0:
                    return (price, None, None)
            except ValueError:
                continue

    return (None, None, None)


def _extract_specs(text: str, input_type: InputType, source_text: str) -> dict[str, str | int | float | bool]:
    """Extract simple specs from text."""
    specs: dict[str, str | int | float | bool] = {}
    text_lower = text.lower()

    # Wireless detection
    if any(kw in text_lower for kw in ["wireless", "сымсыз", "беспроводные"]):
        specs["wireless"] = True

    # Brand detection
    brands = ["Apple", "Sony", "Xiaomi", "Nike", "Samsung", "Adidas"]
    for brand in brands:
        if brand.lower() in text_lower:
            specs["brand"] = brand
            break

    # URL domain extraction
    if input_type == InputType.url:
        try:
            parsed = urlparse(source_text.strip())
            if parsed.netloc:
                specs["source_url_domain"] = parsed.netloc
        except Exception:
            pass

    return specs


def _calculate_confidence(category: IntentCategory, normalized_title: str) -> float:
    """Calculate confidence score based on parsing quality."""
    if category == IntentCategory.other:
        return 0.35

    if normalized_title and len(normalized_title) > 3:
        return 0.85

    return 0.65


def parse_intent_fallback(
    input_text: str,
    user_language: str | None = None,
) -> ParsedIntent:
    """Parse intent using rule-based fallback logic.

    Args:
        input_text: The input text or URL to parse.
        user_language: Optional language hint (kk, ru, en).

    Returns:
        ParsedIntent object with parsed information.

    Raises:
        ValueError: If input_text is empty after stripping.
    """
    # Validate input
    stripped = input_text.strip()
    if not stripped:
        raise ValueError("Input text cannot be empty")

    # Detect input type
    input_type = _detect_input_type(stripped)

    # Detect language
    language = _detect_language(stripped, user_language)

    # Categorize
    category = _categorize_intent(stripped)

    # Normalize title
    normalized_title = _normalize_title(category, stripped, language)
    if not normalized_title:
        normalized_title = "unknown product"

    # Localized title
    localized_title = _localized_title(category, stripped, language)
    if not localized_title:
        localized_title = normalized_title

    # Extract budget
    estimated_price, budget_min, budget_max = _extract_budget(stripped)

    # Extract specs
    specs = _extract_specs(stripped, input_type, stripped)

    # Calculate confidence
    confidence = _calculate_confidence(category, normalized_title)

    # Generate explanation
    if input_type == InputType.url:
        explanation = "Rule-based fallback inferred intent from URL text/domain; no scraping used."
    else:
        explanation = "Rule-based fallback parsed category and budget from input."

    return ParsedIntent(
        input_type=input_type,
        source_text=stripped,
        normalized_title=normalized_title,
        localized_title=localized_title,
        language=language,
        category=category,
        specs=specs,
        estimated_unit_price_kzt=estimated_price,
        budget_min_kzt=budget_min,
        budget_max_kzt=budget_max,
        confidence=confidence,
        parser_mode=ParserMode.rule_based_fallback,
        explanation=explanation,
    )


def parse_cached_demo_intent(
    input_text: str,
    user_language: str | None = None,
) -> ParsedIntent | None:
    """Return cached demo intent if input matches known examples.

    Args:
        input_text: The input text or URL to check.
        user_language: Optional language hint (not used for cache lookup).

    Returns:
        ParsedIntent if cached match found, None otherwise.
    """
    stripped = input_text.strip()
    return _CACHED_DEMO_INTENTS.get(stripped)


def parse_intent(
    input_text: str,
    user_language: str | None = None,
    prefer_cache: bool = True,
) -> ParsedIntent:
    """Parse intent with optional cache preference.

    Args:
        input_text: The input text or URL to parse.
        user_language: Optional language hint (kk, ru, en).
        prefer_cache: If True, check cache first before fallback parsing.

    Returns:
        ParsedIntent object with parsed information.

    Raises:
        ValueError: If input_text is empty after stripping.
    """
    if prefer_cache:
        cached = parse_cached_demo_intent(input_text, user_language)
        if cached is not None:
            return cached

    return parse_intent_fallback(input_text, user_language)
