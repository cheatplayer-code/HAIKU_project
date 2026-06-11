"""Domain model tests."""

import pytest
from pydantic import ValidationError

from app.domain.enums import (
    InputType,
    IntentCategory,
    ParserMode,
    PoolStatus,
    SupportedLanguage,
)
from app.domain.models import (
    CityDemandPoint,
    DemandPoolDto,
    LandedCostBreakdown,
    ParsedIntent,
    PoolMatchResult,
    PoolMatchRuleChecks,
    ProfileIntent,
    SavingsIntervalPercent,
)


class TestParsedIntent:
    """Tests for ParsedIntent model."""

    def test_valid_parsed_intent(self) -> None:
        """Test 1: ParsedIntent valid object can be created."""
        intent = ParsedIntent(
            input_type=InputType.text,
            source_text="Хочу беспроводные наушники",
            normalized_title="wireless headphones",
            localized_title="Беспроводные наушники",
            language=SupportedLanguage.ru,
            category=IntentCategory.electronics,
            specs={"brand": "Sony", "color": "black"},
            estimated_unit_price_kzt=15000,
            budget_min_kzt=10000,
            budget_max_kzt=20000,
            confidence=0.85,
            parser_mode=ParserMode.cache_fallback,
            explanation="Inferred from Russian text input",
        )
        assert intent.normalized_title == "wireless headphones"
        assert intent.confidence == 0.85

    def test_rejects_empty_normalized_title(self) -> None:
        """Test 2: ParsedIntent rejects empty normalized_title."""
        with pytest.raises(ValidationError):
            ParsedIntent(
                input_type=InputType.text,
                source_text="test",
                normalized_title="",
                localized_title="test",
                language=SupportedLanguage.en,
                category=IntentCategory.other,
                confidence=0.5,
                parser_mode=ParserMode.rule_based_fallback,
                explanation="test",
            )

    def test_rejects_confidence_greater_than_one(self) -> None:
        """Test 3: ParsedIntent rejects confidence > 1."""
        with pytest.raises(ValidationError):
            ParsedIntent(
                input_type=InputType.text,
                source_text="test",
                normalized_title="test product",
                localized_title="test product",
                language=SupportedLanguage.en,
                category=IntentCategory.other,
                confidence=1.5,
                parser_mode=ParserMode.rule_based_fallback,
                explanation="test",
            )

    def test_rejects_negative_price(self) -> None:
        """Test 4: ParsedIntent rejects negative price."""
        with pytest.raises(ValidationError):
            ParsedIntent(
                input_type=InputType.text,
                source_text="test",
                normalized_title="test product",
                localized_title="test product",
                language=SupportedLanguage.en,
                category=IntentCategory.other,
                estimated_unit_price_kzt=-100,
                confidence=0.5,
                parser_mode=ParserMode.rule_based_fallback,
                explanation="test",
            )

    def test_rejects_budget_min_greater_than_budget_max(self) -> None:
        """Test 5: ParsedIntent rejects budget_min_kzt > budget_max_kzt."""
        with pytest.raises(ValidationError):
            ParsedIntent(
                input_type=InputType.text,
                source_text="test",
                normalized_title="test product",
                localized_title="test product",
                language=SupportedLanguage.en,
                category=IntentCategory.other,
                budget_min_kzt=20000,
                budget_max_kzt=10000,
                confidence=0.5,
                parser_mode=ParserMode.rule_based_fallback,
                explanation="test",
            )


class TestDemandPoolDto:
    """Tests for DemandPoolDto model."""

    def test_valid_demand_pool(self) -> None:
        """Test 6: DemandPoolDto valid object can be created."""
        savings = SavingsIntervalPercent(min=28, max=36)
        pool = DemandPoolDto(
            id="pool-001",
            city="Almaty",
            category=IntentCategory.electronics,
            title="wireless headphones",
            localized_title="Беспроводные наушники",
            status=PoolStatus.forming,
            current_intent_count=24,
            moq=25,
            missing_to_moq=1,
            estimated_retail_price_kzt=15000,
            estimated_group_price_kzt=9900,
            estimated_savings_percent=34,
            savings_interval_percent=savings,
        )
        assert pool.id == "pool-001"
        assert pool.missing_to_moq == 1

    def test_computes_missing_to_moq_correctly_24_25(self) -> None:
        """Test 7: DemandPoolDto computes/validates missing_to_moq correctly for 24/25."""
        savings = SavingsIntervalPercent(min=28, max=36)
        # Correct case: 24/25 means missing_to_moq should be 1
        pool = DemandPoolDto(
            id="pool-001",
            city="Almaty",
            category=IntentCategory.electronics,
            title="wireless headphones",
            localized_title="Беспроводные наушники",
            status=PoolStatus.forming,
            current_intent_count=24,
            moq=25,
            missing_to_moq=1,
            estimated_retail_price_kzt=15000,
            estimated_group_price_kzt=9900,
            estimated_savings_percent=34,
            savings_interval_percent=savings,
        )
        assert pool.missing_to_moq == 1

        # Should reject wrong missing_to_moq
        with pytest.raises(ValidationError) as exc_info:
            DemandPoolDto(
                id="pool-002",
                city="Almaty",
                category=IntentCategory.electronics,
                title="wireless headphones",
                localized_title="Беспроводные наушники",
                status=PoolStatus.forming,
                current_intent_count=24,
                moq=25,
                missing_to_moq=5,  # Wrong: should be 1
                estimated_retail_price_kzt=15000,
                estimated_group_price_kzt=9900,
                estimated_savings_percent=34,
                savings_interval_percent=savings,
            )
        assert "missing_to_moq should be 1" in str(exc_info.value)

    def test_rejects_group_price_greater_than_retail(self) -> None:
        """Test 8: DemandPoolDto rejects group price greater than retail price."""
        savings = SavingsIntervalPercent(min=28, max=36)
        with pytest.raises(ValidationError) as exc_info:
            DemandPoolDto(
                id="pool-001",
                city="Almaty",
                category=IntentCategory.electronics,
                title="wireless headphones",
                localized_title="Беспроводные наушники",
                status=PoolStatus.forming,
                current_intent_count=24,
                moq=25,
                missing_to_moq=1,
                estimated_retail_price_kzt=10000,
                estimated_group_price_kzt=15000,  # Greater than retail
                estimated_savings_percent=34,
                savings_interval_percent=savings,
            )
        assert "estimated_group_price_kzt must be <= estimated_retail_price_kzt" in str(
            exc_info.value
        )

    def test_rejects_moq_less_than_or_equal_zero(self) -> None:
        """Test 9: DemandPoolDto rejects moq <= 0."""
        savings = SavingsIntervalPercent(min=28, max=36)
        with pytest.raises(ValidationError):
            DemandPoolDto(
                id="pool-001",
                city="Almaty",
                category=IntentCategory.electronics,
                title="wireless headphones",
                localized_title="Беспроводные наушники",
                status=PoolStatus.forming,
                current_intent_count=0,
                moq=0,
                missing_to_moq=0,
                estimated_retail_price_kzt=15000,
                estimated_group_price_kzt=9900,
                estimated_savings_percent=34,
                savings_interval_percent=savings,
            )


class TestSavingsIntervalPercent:
    """Tests for SavingsIntervalPercent model."""

    def test_rejects_min_greater_than_max(self) -> None:
        """Test 10: SavingsIntervalPercent rejects min > max."""
        with pytest.raises(ValidationError) as exc_info:
            SavingsIntervalPercent(min=50, max=30)
        assert "min must be <= max" in str(exc_info.value)


class TestPoolMatchResult:
    """Tests for PoolMatchResult model."""

    def test_requires_pool_when_matched_true(self) -> None:
        """Test 11: PoolMatchResult requires pool when matched_existing_pool=True."""
        rule_checks = PoolMatchRuleChecks(
            city_matched=True,
            category_matched=True,
            budget_overlapped=True,
            similarity_passed=True,
        )
        with pytest.raises(ValidationError) as exc_info:
            PoolMatchResult(
                matched_existing_pool=True,
                similarity_score=0.85,
                rule_checks=rule_checks,
                pool=None,
            )
        assert "pool must not be None" in str(exc_info.value)


class TestLandedCostBreakdown:
    """Tests for LandedCostBreakdown model."""

    def test_validates_total_equals_sum(self) -> None:
        """Test 12: LandedCostBreakdown validates total = product + cargo + duty."""
        breakdown = LandedCostBreakdown(
            product_price_kzt=10000,
            cargo_estimate_kzt=1500,
            duty_estimate_kzt=500,
            total_landed_cost_kzt=12000,
            note="Demo estimate, not customs-accurate",
        )
        assert breakdown.total_landed_cost_kzt == 12000

        with pytest.raises(ValidationError) as exc_info:
            LandedCostBreakdown(
                product_price_kzt=10000,
                cargo_estimate_kzt=1500,
                duty_estimate_kzt=500,
                total_landed_cost_kzt=13000,  # Wrong total
                note="Demo estimate, not customs-accurate",
            )
        assert "total_landed_cost_kzt must equal sum of components" in str(exc_info.value)


class TestCityDemandPoint:
    """Tests for CityDemandPoint model."""

    def test_rejects_invalid_lat_lng(self) -> None:
        """Test 13: CityDemandPoint rejects invalid lat/lng."""
        # Invalid latitude (> 90)
        with pytest.raises(ValidationError):
            CityDemandPoint(lat=95.0, lng=76.0, weight=0.5)

        # Invalid longitude (> 180)
        with pytest.raises(ValidationError):
            CityDemandPoint(lat=43.0, lng=200.0, weight=0.5)

        # Invalid weight (> 1)
        with pytest.raises(ValidationError):
            CityDemandPoint(lat=43.0, lng=76.0, weight=1.5)


class TestProfileIntent:
    """Tests for ProfileIntent model."""

    def test_valid_profile_intent(self) -> None:
        """Test 14: ProfileIntent valid object can be created."""
        intent = ProfileIntent(
            id="intent-001",
            title="wireless headphones",
            localized_title="Беспроводные наушники",
            city="Almaty",
            category=IntentCategory.electronics,
            pool_id="pool-001",
            pool_status=PoolStatus.forming,
            created_at="2025-01-15T10:30:00Z",
        )
        assert intent.id == "intent-001"
        assert intent.city == "Almaty"
        assert intent.is_demo_data is True


class TestEnumValues:
    """Tests for enum values matching API_CONTRACT.md."""

    def test_intent_category_values(self) -> None:
        """Test 15a: IntentCategory values match API_CONTRACT.md exactly."""
        expected = {
            "electronics",
            "home",
            "fashion",
            "beauty",
            "sports",
            "kids",
            "auto",
            "books",
            "other",
        }
        actual = {e.value for e in IntentCategory}
        assert actual == expected

    def test_parser_mode_values(self) -> None:
        """Test 15b: ParserMode values match API_CONTRACT.md exactly."""
        expected = {"live_llm", "cache_fallback", "rule_based_fallback"}
        actual = {e.value for e in ParserMode}
        assert actual == expected

    def test_pool_status_values(self) -> None:
        """Test 15c: PoolStatus values match API_CONTRACT.md exactly."""
        expected = {"forming", "ready", "deal_formed", "closed"}
        actual = {e.value for e in PoolStatus}
        assert actual == expected

    def test_input_type_values(self) -> None:
        """Test 15d: InputType values match API_CONTRACT.md exactly."""
        expected = {"url", "text"}
        actual = {e.value for e in InputType}
        assert actual == expected

    def test_supported_language_values(self) -> None:
        """Test 15e: SupportedLanguage values match API_CONTRACT.md exactly."""
        expected = {"kk", "ru", "en", "unknown"}
        actual = {e.value for e in SupportedLanguage}
        assert actual == expected


class TestNoApiEndpointsAdded:
    """Test 16: app.main still exposes only /health; no product API endpoints."""

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
