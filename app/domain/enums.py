"""Birge domain enums."""

from enum import Enum


class IntentCategory(str, Enum):
    """Allowed intent categories."""

    electronics = "electronics"
    home = "home"
    fashion = "fashion"
    beauty = "beauty"
    sports = "sports"
    kids = "kids"
    auto = "auto"
    books = "books"
    other = "other"


class ParserMode(str, Enum):
    """Parser execution modes."""

    live_llm = "live_llm"
    cache_fallback = "cache_fallback"
    rule_based_fallback = "rule_based_fallback"


class PoolStatus(str, Enum):
    """Demand pool status values."""

    forming = "forming"
    ready = "ready"
    deal_formed = "deal_formed"
    closed = "closed"


class InputType(str, Enum):
    """Input type for intent parsing."""

    url = "url"
    text = "text"


class SupportedLanguage(str, Enum):
    """Supported languages for intent parsing."""

    kk = "kk"
    ru = "ru"
    en = "en"
    unknown = "unknown"
