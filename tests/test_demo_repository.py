"""Tests for demo repository."""

from app.domain.enums import IntentCategory
from app.domain.models import ProfileIntent
from app.repositories.demo_repository import DemoRepository
from app.services.pricing import estimate_group_price_kzt


class TestDemoRepositorySeeding:
    """Tests for DemoRepository seeding."""

    def test_seeds_at_least_8_pools(self):
        """DemoRepository seeds at least 8 pools."""
        repo = DemoRepository()
        assert len(repo.pools) >= 8

    def test_required_headphones_pool_exists(self):
        """Required headphones pool exists."""
        repo = DemoRepository()
        pool = repo.get_pool("pool-almaty-headphones")
        assert pool is not None
        assert pool.city == "Almaty"
        assert pool.category == IntentCategory.electronics
        assert "headphone" in pool.title.lower() or "наушник" in pool.localized_title.lower()

    def test_required_headphones_pool_is_24_of_25_missing_1(self):
        """Required headphones pool is 24/25 and missing_to_moq=1."""
        repo = DemoRepository()
        pool = repo.get_pool("pool-almaty-headphones")
        assert pool is not None
        assert pool.current_intent_count == 24
        assert pool.moq == 25
        assert pool.missing_to_moq == 1

    def test_required_headphones_group_price_calculated_using_pricing_helper(self):
        """Required headphones group price is calculated using pricing helper."""
        repo = DemoRepository()
        pool = repo.get_pool("pool-almaty-headphones")
        assert pool is not None
        
        expected_price = estimate_group_price_kzt(
            pool.estimated_retail_price_kzt,
            pool.category
        )
        assert pool.estimated_group_price_kzt == expected_price

    def test_all_seeded_pools_are_is_demo_data_true(self):
        """All seeded pools are is_demo_data=True."""
        repo = DemoRepository()
        for pool in repo.pools.values():
            assert pool.is_demo_data is True


class TestListPools:
    """Tests for list_pools method."""

    def test_list_pools_almaty_returns_only_almaty_pools(self):
        """list_pools("Almaty") returns only Almaty pools."""
        repo = DemoRepository()
        pools = repo.list_pools("Almaty")
        
        assert len(pools) > 0
        for pool in pools:
            assert pool.city.lower() == "almaty"

    def test_list_pools_almaty_electronics_filters_category(self):
        """list_pools("Almaty", IntentCategory.electronics) filters category."""
        repo = DemoRepository()
        pools = repo.list_pools("Almaty", IntentCategory.electronics)
        
        assert len(pools) > 0
        for pool in pools:
            assert pool.city.lower() == "almaty"
            assert pool.category == IntentCategory.electronics

    def test_list_pools_respects_limit(self):
        """list_pools respects limit."""
        repo = DemoRepository()
        pools = repo.list_pools("Almaty", limit=3)
        assert len(pools) <= 3

    def test_list_pools_ordering_closer_to_moq_first(self):
        """list_pools ordering puts closer-to-MOQ pools first."""
        repo = DemoRepository()
        pools = repo.list_pools("Almaty")
        
        # Check that pools are sorted by missing_to_moq ascending
        for i in range(len(pools) - 1):
            assert pools[i].missing_to_moq <= pools[i + 1].missing_to_moq

    def test_list_pools_case_insensitive_city(self):
        """City filter is case-insensitive."""
        repo = DemoRepository()
        pools_lower = repo.list_pools("almaty")
        pools_upper = repo.list_pools("ALMATY")
        pools_mixed = repo.list_pools("AlMaTy")
        
        assert len(pools_lower) == len(pools_upper) == len(pools_mixed)
        assert len(pools_lower) > 0


class TestGetPool:
    """Tests for get_pool method."""

    def test_get_pool_returns_none_for_missing_id(self):
        """get_pool returns None for missing id."""
        repo = DemoRepository()
        pool = repo.get_pool("non-existent-pool-id")
        assert pool is None

    def test_get_pool_returns_existing_pool(self):
        """get_pool returns existing pool."""
        repo = DemoRepository()
        pool = repo.get_pool("pool-almaty-headphones")
        assert pool is not None
        assert pool.id == "pool-almaty-headphones"


class TestUpdatePool:
    """Tests for update_pool method."""

    def test_update_pool_stores_updated_pool(self):
        """update_pool stores updated pool."""
        repo = DemoRepository()
        original_pool = repo.get_pool("pool-almaty-headphones")
        assert original_pool is not None
        
        # Create an updated version
        updated_pool = original_pool.model_copy(
            update={"current_intent_count": 25, "missing_to_moq": 0}
        )
        
        repo.update_pool(updated_pool)
        
        retrieved_pool = repo.get_pool("pool-almaty-headphones")
        assert retrieved_pool is not None
        assert retrieved_pool.current_intent_count == 25
        assert retrieved_pool.missing_to_moq == 0


class TestUserIntents:
    """Tests for user intent methods."""

    def test_list_user_intents_returns_empty_list_for_new_esim_profile_id(self):
        """list_user_intents returns empty list for new esim_profile_id."""
        repo = DemoRepository()
        intents = repo.list_user_intents("new-esim-profile-id")
        assert intents == []

    def test_add_user_intent_stores_profile_intent_under_esim_profile_id(self):
        """add_user_intent stores ProfileIntent under esim_profile_id."""
        repo = DemoRepository()
        esim_profile_id = "test-esim-profile"
        
        intent = ProfileIntent(
            id="intent-1",
            title="test item",
            localized_title="тестовый товар",
            city="Almaty",
            category=IntentCategory.other,
            created_at="2024-01-01T00:00:00Z",
        )
        
        repo.add_user_intent(esim_profile_id, intent)
        
        stored_intents = repo.list_user_intents(esim_profile_id)
        assert len(stored_intents) == 1
        assert stored_intents[0].id == "intent-1"
        assert stored_intents[0].title == "test item"

    def test_add_multiple_user_intents(self):
        """Multiple intents can be added for same profile."""
        repo = DemoRepository()
        esim_profile_id = "test-esim-profile-multi"
        
        intent1 = ProfileIntent(
            id="intent-1",
            title="item one",
            localized_title="первый товар",
            city="Almaty",
            category=IntentCategory.other,
            created_at="2024-01-01T00:00:00Z",
        )
        
        intent2 = ProfileIntent(
            id="intent-2",
            title="item two",
            localized_title="второй товар",
            city="Astana",
            category=IntentCategory.books,
            created_at="2024-01-02T00:00:00Z",
        )
        
        repo.add_user_intent(esim_profile_id, intent1)
        repo.add_user_intent(esim_profile_id, intent2)
        
        stored_intents = repo.list_user_intents(esim_profile_id)
        assert len(stored_intents) == 2


class TestApiRoutesAfterPhaseEight:
    """Test that Phase 8 API routes are registered without removing health."""

    def test_app_main_exposes_health_and_api_routes(self):
        """app.main exposes /health and Phase 8 API endpoints."""
        from app.main import app
        
        routes = sorted(route.path for route in app.routes)
        assert "/health" in routes
        assert "/api/intent/parse" in routes
        assert "/api/pools/match" in routes
        assert "/api/intents" in routes
        assert "/api/pools" in routes
        assert "/api/profile/intents" in routes
