"""Pool matcher service tests."""

from app.domain.enums import IntentCategory, PoolStatus
from app.domain.models import DemandPoolDto, ParsedIntent, SavingsIntervalPercent
from app.services.pool_matcher import (
    calculate_keyword_similarity,
    match_intent_to_pool,
)


# Helper to create test pools
def _make_pool(
    pool_id: str,
    city: str,
    category: IntentCategory,
    title: str,
    localized_title: str,
    status: PoolStatus = PoolStatus.forming,
    current_intent_count: int = 10,
    moq: int = 25,
    estimated_retail_price_kzt: int = 20000,
    estimated_savings_percent: int = 34,
) -> DemandPoolDto:
    """Create a test DemandPoolDto."""
    savings = SavingsIntervalPercent(min=28, max=36)
    return DemandPoolDto.from_counts(
        id=pool_id,
        city=city,
        category=category,
        title=title,
        localized_title=localized_title,
        status=status,
        current_intent_count=current_intent_count,
        moq=moq,
        estimated_retail_price_kzt=estimated_retail_price_kzt,
        estimated_savings_percent=estimated_savings_percent,
        savings_interval_percent=savings,
    )


# Helper to create test intents
def _make_intent(
    source_text: str,
    normalized_title: str,
    localized_title: str,
    category: IntentCategory,
    budget_max_kzt: int | None = None,
) -> ParsedIntent:
    """Create a test ParsedIntent."""
    from app.domain.enums import InputType, ParserMode, SupportedLanguage
    
    return ParsedIntent(
        input_type=InputType.text,
        source_text=source_text,
        normalized_title=normalized_title,
        localized_title=localized_title,
        language=SupportedLanguage.en,
        category=category,
        specs={},
        estimated_unit_price_kzt=None,
        budget_min_kzt=None,
        budget_max_kzt=budget_max_kzt,
        confidence=0.85,
        parser_mode=ParserMode.rule_based_fallback,
        explanation="Test intent",
    )


class TestHeadphonesMatch:
    """Test 1: Headphones intent matches Almaty headphones pool."""

    def test_headphones_intent_matches_almaty_headphones_pool(self) -> None:
        """Headphones intent should match wireless headphones pool in Almaty."""
        # Create the required killer demo pool
        pool = _make_pool(
            pool_id="pool-almaty-headphones",
            city="Almaty",
            category=IntentCategory.electronics,
            title="wireless headphones",
            localized_title="Беспроводные наушники",
            current_intent_count=24,
            moq=25,
        )
        
        # Create headphones intent
        intent = _make_intent(
            source_text="I want wireless headphones",
            normalized_title="wireless headphones",
            localized_title="Беспроводные наушники",
            category=IntentCategory.electronics,
        )
        
        result = match_intent_to_pool(intent, [pool], "Almaty")
        
        assert result.matched_existing_pool is True
        assert result.pool is not None
        assert result.pool.id == "pool-almaty-headphones"
        assert result.similarity_score > 0.45


class TestDifferentCityNoMatch:
    """Test 2: Different city does not match."""

    def test_different_city_does_not_match(self) -> None:
        """Intent for Almaty should not match Astana pool."""
        pool = _make_pool(
            pool_id="pool-astana-headphones",
            city="Astana",
            category=IntentCategory.electronics,
            title="wireless headphones",
            localized_title="Беспроводные наушники",
        )
        
        intent = _make_intent(
            source_text="I want wireless headphones",
            normalized_title="wireless headphones",
            localized_title="Беспроводные наушники",
            category=IntentCategory.electronics,
        )
        
        result = match_intent_to_pool(intent, [pool], "Almaty")
        
        assert result.matched_existing_pool is False
        assert result.pool is None


class TestDifferentCategoryNoMatch:
    """Test 3: Different category does not match."""

    def test_different_category_does_not_match(self) -> None:
        """Electronics intent should not match home category pool."""
        pool = _make_pool(
            pool_id="pool-almaty-humidifier",
            city="Almaty",
            category=IntentCategory.home,
            title="home humidifier",
            localized_title="Увлажнитель воздуха",
        )
        
        intent = _make_intent(
            source_text="I want wireless headphones",
            normalized_title="wireless headphones",
            localized_title="Беспроводные наушники",
            category=IntentCategory.electronics,
        )
        
        result = match_intent_to_pool(intent, [pool], "Almaty")
        
        assert result.matched_existing_pool is False
        assert result.pool is None


class TestClosedPoolNoMatch:
    """Test 4: Closed pool does not match."""

    def test_closed_pool_does_not_match(self) -> None:
        """Closed pool should not be matched."""
        pool = _make_pool(
            pool_id="pool-closed",
            city="Almaty",
            category=IntentCategory.electronics,
            title="wireless headphones",
            localized_title="Беспроводные наушники",
            status=PoolStatus.closed,
        )
        
        intent = _make_intent(
            source_text="I want wireless headphones",
            normalized_title="wireless headphones",
            localized_title="Беспроводные наушники",
            category=IntentCategory.electronics,
        )
        
        result = match_intent_to_pool(intent, [pool], "Almaty")
        
        assert result.matched_existing_pool is False
        assert result.pool is None


class TestDealFormedPoolNoMatch:
    """Test 5: Deal-formed pool does not match."""

    def test_deal_formed_pool_does_not_match(self) -> None:
        """Deal-formed pool should not be matched."""
        pool = _make_pool(
            pool_id="pool-deal-formed",
            city="Almaty",
            category=IntentCategory.electronics,
            title="wireless headphones",
            localized_title="Беспроводные наушники",
            status=PoolStatus.deal_formed,
        )
        
        intent = _make_intent(
            source_text="I want wireless headphones",
            normalized_title="wireless headphones",
            localized_title="Беспроводные наушники",
            category=IntentCategory.electronics,
        )
        
        result = match_intent_to_pool(intent, [pool], "Almaty")
        
        assert result.matched_existing_pool is False
        assert result.pool is None


class TestBudgetTooLow:
    """Test 6: Budget too low fails budget overlap."""

    def test_budget_too_low_fails_overlap(self) -> None:
        """Intent with very low budget should not match expensive pool."""
        # Pool with group price ~13200 (20000 * 0.66)
        pool = _make_pool(
            pool_id="pool-expensive",
            city="Almaty",
            category=IntentCategory.electronics,
            title="wireless headphones",
            localized_title="Беспроводные наушники",
            estimated_retail_price_kzt=20000,
            estimated_savings_percent=34,
        )
        
        # Intent with max budget 5000 (below 80% of ~13200 = ~10560)
        intent = _make_intent(
            source_text="I want cheap headphones",
            normalized_title="wireless headphones",
            localized_title="Беспроводные наушники",
            category=IntentCategory.electronics,
            budget_max_kzt=5000,
        )
        
        result = match_intent_to_pool(intent, [pool], "Almaty")
        
        assert result.matched_existing_pool is False
        assert result.pool is None


class TestMissingBudgetAllowsMatching:
    """Test 7: Missing budget still allows matching."""

    def test_missing_budget_allows_matching(self) -> None:
        """Intent without budget should match based on other criteria."""
        pool = _make_pool(
            pool_id="pool-almaty-headphones",
            city="Almaty",
            category=IntentCategory.electronics,
            title="wireless headphones",
            localized_title="Беспроводные наушники",
        )
        
        intent = _make_intent(
            source_text="I want wireless headphones",
            normalized_title="wireless headphones",
            localized_title="Беспроводные наушники",
            category=IntentCategory.electronics,
            budget_max_kzt=None,
        )
        
        result = match_intent_to_pool(intent, [pool], "Almaty")
        
        assert result.matched_existing_pool is True
        assert result.pool is not None


class TestSimilarityClamped:
    """Test 8: Similarity score is clamped 0..1."""

    def test_similarity_clamped_zero_to_one(self) -> None:
        """Similarity score should always be between 0 and 1."""
        pool = _make_pool(
            pool_id="pool-test",
            city="Almaty",
            category=IntentCategory.electronics,
            title="wireless headphones",
            localized_title="Беспроводные наушники",
        )
        
        intent = _make_intent(
            source_text="I want wireless headphones",
            normalized_title="wireless headphones",
            localized_title="Беспроводные наушники",
            category=IntentCategory.electronics,
        )
        
        similarity = calculate_keyword_similarity(intent, pool)
        
        assert 0.0 <= similarity <= 1.0


class TestUnrelatedIntentNoMatch:
    """Test 9: Unrelated weird intent returns matched_existing_pool=False."""

    def test_unrelated_weird_intent_no_match(self) -> None:
        """Unrelated intent should not match any pool."""
        pool = _make_pool(
            pool_id="pool-headphones",
            city="Almaty",
            category=IntentCategory.electronics,
            title="wireless headphones",
            localized_title="Беспроводные наушники",
        )
        
        intent = _make_intent(
            source_text="I need car tires for winter",
            normalized_title="car tires",
            localized_title="Зимние шины",
            category=IntentCategory.auto,
        )
        
        result = match_intent_to_pool(intent, [pool], "Almaty")
        
        assert result.matched_existing_pool is False


class TestMultiplePoolsHighestSimilarity:
    """Test 10: Multiple matching pools choose highest similarity."""

    def test_multiple_pools_chooses_highest_similarity(self) -> None:
        """When multiple pools match, choose the one with highest similarity."""
        # Pool with exact match
        pool_exact = _make_pool(
            pool_id="pool-exact",
            city="Almaty",
            category=IntentCategory.electronics,
            title="wireless headphones",
            localized_title="Беспроводные наушники",
            current_intent_count=10,
        )
        
        # Pool with partial match
        pool_partial = _make_pool(
            pool_id="pool-partial",
            city="Almaty",
            category=IntentCategory.electronics,
            title="bluetooth earbuds",
            localized_title="Bluetooth наушники",
            current_intent_count=10,
        )
        
        intent = _make_intent(
            source_text="I want wireless headphones",
            normalized_title="wireless headphones",
            localized_title="Беспроводные наушники",
            category=IntentCategory.electronics,
        )
        
        result = match_intent_to_pool(intent, [pool_exact, pool_partial], "Almaty")
        
        assert result.matched_existing_pool is True
        assert result.pool is not None
        assert result.pool.id == "pool-exact"


class TestTieChoosesCloserToMoq:
    """Test 11: Tie chooses pool closer to MOQ."""

    def test_tie_chooses_closer_to_moq(self) -> None:
        """When similarity is tied, choose pool closer to MOQ."""
        # Two identical pools except for current_intent_count
        pool_far = _make_pool(
            pool_id="pool-far",
            city="Almaty",
            category=IntentCategory.electronics,
            title="wireless headphones",
            localized_title="Беспроводные наушники",
            current_intent_count=5,
            moq=25,
        )
        
        pool_close = _make_pool(
            pool_id="pool-close",
            city="Almaty",
            category=IntentCategory.electronics,
            title="wireless headphones",
            localized_title="Беспроводные наушники",
            current_intent_count=20,
            moq=25,
        )
        
        intent = _make_intent(
            source_text="I want wireless headphones",
            normalized_title="wireless headphones",
            localized_title="Беспроводные наушники",
            category=IntentCategory.electronics,
        )
        
        result = match_intent_to_pool(intent, [pool_far, pool_close], "Almaty")
        
        assert result.matched_existing_pool is True
        assert result.pool is not None
        assert result.pool.id == "pool-close"


class TestNoMutation:
    """Test 12: match_intent_to_pool does not mutate input pools."""

    def test_no_mutation_of_input_pools(self) -> None:
        """match_intent_to_pool should not mutate input pools."""
        pool = _make_pool(
            pool_id="pool-test",
            city="Almaty",
            category=IntentCategory.electronics,
            title="wireless headphones",
            localized_title="Беспроводные наушники",
            current_intent_count=10,
        )
        
        # Store original values
        original_count = pool.current_intent_count
        original_missing = pool.missing_to_moq
        
        intent = _make_intent(
            source_text="I want wireless headphones",
            normalized_title="wireless headphones",
            localized_title="Беспроводные наушники",
            category=IntentCategory.electronics,
        )
        
        match_intent_to_pool(intent, [pool], "Almaty")
        
        # Verify no mutation
        assert pool.current_intent_count == original_count
        assert pool.missing_to_moq == original_missing


class TestRuleChecksIncluded:
    """Test 13: PoolMatchResult includes rule_checks."""

    def test_rule_checks_included_in_result(self) -> None:
        """PoolMatchResult should include detailed rule_checks."""
        pool = _make_pool(
            pool_id="pool-test",
            city="Almaty",
            category=IntentCategory.electronics,
            title="wireless headphones",
            localized_title="Беспроводные наушники",
        )
        
        intent = _make_intent(
            source_text="I want wireless headphones",
            normalized_title="wireless headphones",
            localized_title="Беспроводные наушники",
            category=IntentCategory.electronics,
        )
        
        result = match_intent_to_pool(intent, [pool], "Almaty")
        
        assert result.rule_checks.city_matched is True
        assert result.rule_checks.category_matched is True
        assert result.rule_checks.budget_overlapped is True
        assert result.rule_checks.similarity_passed is True


class TestPhaseEightApiEndpointsAdded:
    """Test 14: app.main exposes health and Phase 8 API endpoints."""

    def test_health_and_api_endpoints_exist(self) -> None:
        """Verify Phase 8 API endpoints are registered."""
        from app.main import app

        routes = sorted(route.path for route in app.routes)
        assert "/health" in routes
        assert "/api/intent/parse" in routes
        assert "/api/pools/match" in routes
        assert "/api/intents" in routes
        assert "/api/pools" in routes
        assert "/api/profile/intents" in routes
