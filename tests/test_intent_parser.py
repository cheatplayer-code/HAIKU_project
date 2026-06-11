"""Intent parser tests."""

import pytest

from app.domain.enums import InputType, IntentCategory, ParserMode, SupportedLanguage
from app.services.intent_parser import (
    parse_intent,
    parse_intent_fallback,
    parse_cached_demo_intent,
)


class TestEmptyInput:
    """Test 1: Empty input raises ValueError."""

    def test_empty_input_raises_value_error(self) -> None:
        """Empty input should raise ValueError."""
        with pytest.raises(ValueError):
            parse_intent_fallback("")

        with pytest.raises(ValueError):
            parse_intent_fallback("   ")

        with pytest.raises(ValueError):
            parse_intent("  \t\n  ")


class TestRussianHeadphones:
    """Test 2: Russian headphones text parsing."""

    def test_russian_headphones_parses_correctly(self) -> None:
        """Russian headphones text should parse correctly."""
        result = parse_intent_fallback("Хочу беспроводные наушники до 15000 тенге")

        assert result.category == IntentCategory.electronics
        assert result.normalized_title == "wireless headphones"
        assert result.localized_title == "Беспроводные наушники"
        assert result.language == SupportedLanguage.ru
        assert result.parser_mode == ParserMode.rule_based_fallback


class TestKazakhHumidifier:
    """Test 3: Kazakh humidifier text parsing."""

    def test_kazakh_humidifier_parses_correctly(self) -> None:
        """Kazakh humidifier text should parse correctly."""
        result = parse_intent_fallback("Маған үйге ауа ылғалдатқыш керек")

        assert result.language == SupportedLanguage.kk
        assert result.category == IntentCategory.home
        assert result.normalized_title == "home humidifier"
        assert result.localized_title == "Ауа ылғалдатқыш"


class TestEnglishProjector:
    """Test 4: English projector text parsing."""

    def test_english_projector_parses_correctly(self) -> None:
        """English projector text should parse correctly."""
        result = parse_intent_fallback("I want a cheap portable projector")

        assert result.language == SupportedLanguage.en
        assert result.category == IntentCategory.electronics
        assert result.normalized_title == "portable projector"


class TestUrlInput:
    """Tests 5-6: URL input detection."""

    def test_url_detects_input_type_url(self) -> None:
        """URL input should detect InputType.url."""
        result = parse_intent_fallback("https://example.com/headphones-demo")

        assert result.input_type == InputType.url

    def test_url_does_not_claim_scraping(self) -> None:
        """URL input explanation should not claim scraping."""
        result = parse_intent_fallback("https://example.com/some-product")

        assert "scraping" not in result.explanation.lower() or "no scraping" in result.explanation.lower()
        assert "no scraping used" in result.explanation


class TestBudgetExtraction:
    """Tests 7-8: Budget extraction."""

    def test_budget_do_15000_tenge_sets_max(self) -> None:
        """'до 15000 тенге' should set budget_max_kzt=15000."""
        result = parse_intent_fallback("Хочу наушники до 15000 тенге")

        assert result.budget_max_kzt == 15000
        assert result.budget_min_kzt is None

    def test_under_15k_sets_budget_max(self) -> None:
        """'under 15k' should set budget_max_kzt=15000."""
        result = parse_intent_fallback("I want headphones under 15k")

        assert result.budget_max_kzt == 15000


class TestBrandExtraction:
    """Test 9: Brand extraction."""

    def test_brand_extraction_sony(self) -> None:
        """Brand 'Sony' should be extracted from text."""
        result = parse_intent_fallback("I want Sony headphones")

        assert result.specs.get("brand") == "Sony"

    def test_brand_extraction_xiaomi(self) -> None:
        """Brand 'Xiaomi' should be extracted from text."""
        result = parse_intent_fallback("Нужны наушники Xiaomi")

        assert result.specs.get("brand") == "Xiaomi"

    def test_brand_extraction_nike(self) -> None:
        """Brand 'Nike' should be extracted from text."""
        result = parse_intent_fallback("I need Nike shoes")

        assert result.specs.get("brand") == "Nike"


class TestUnknownInput:
    """Test 10: Unknown weird input."""

    def test_unknown_input_returns_other_category(self) -> None:
        """Weird unknown input should return category 'other' and low confidence."""
        result = parse_intent_fallback("asdf qwerty zxcvbnm random gibberish")

        assert result.category == IntentCategory.other
        assert result.confidence <= 0.35


class TestCachedDemo:
    """Tests 11-12: Cached demo examples."""

    def test_cached_demo_url_returns_cache_fallback(self) -> None:
        """Cached demo URL should return ParserMode.cache_fallback."""
        result = parse_cached_demo_intent("https://example.com/headphones-demo")

        assert result is not None
        assert result.parser_mode == ParserMode.cache_fallback
        assert result.normalized_title == "wireless headphones"

    def test_parse_intent_with_prefer_cache_false_returns_rule_based(self) -> None:
        """parse_intent with prefer_cache=False should return rule_based_fallback."""
        # This is a cached example, but with prefer_cache=False it should use fallback
        result = parse_intent(
            "https://example.com/headphones-demo",
            prefer_cache=False,
        )

        assert result.parser_mode == ParserMode.rule_based_fallback

    def test_parse_intent_with_prefer_cache_true_returns_cache(self) -> None:
        """parse_intent with prefer_cache=True should return cache_fallback for known examples."""
        result = parse_intent(
            "https://example.com/headphones-demo",
            prefer_cache=True,
        )

        assert result.parser_mode == ParserMode.cache_fallback


class TestNoPurchaseClaims:
    """Test 13: Parser never claims purchase/order/payment/reservation."""

    def test_parser_never_claims_purchase(self) -> None:
        """Parser explanation should never claim purchase, order, payment, or reservation."""
        test_inputs = [
            "Хочу купить наушники",
            "I want to buy headphones",
            "Маған құлаққап сатып алу керек",
            "https://example.com/product",
            "Заказать кроссовки",
        ]

        forbidden_words = {"buy", "bought", "purchase", "order", "ordered", "payment", "pay", "reserve", "reserved"}

        for input_text in test_inputs:
            result = parse_intent_fallback(input_text)
            explanation_lower = result.explanation.lower()

            for word in forbidden_words:
                assert word not in explanation_lower, (
                    f"Explanation should not contain '{word}' for input '{input_text}'. "
                    f"Got: {result.explanation}"
                )


class TestNoApiEndpointsAdded:
    """Test 14: app.main still exposes only /health; no product API endpoints."""

    def test_only_health_endpoint_exists(self) -> None:
        """Verify no API endpoints were added in this phase."""
        from app.main import app

        routes = sorted(route.path for route in app.routes)
        assert "/health" in routes
        assert "/api/intent/parse" not in routes
        assert "/api/pools/match" not in routes
        assert "/api/intents" not in routes
        assert "/api/pools" not in routes
        assert "/api/profile/intents" not in routes
