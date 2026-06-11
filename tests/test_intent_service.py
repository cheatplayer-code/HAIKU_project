"""Tests for intent join orchestration."""

from __future__ import annotations

import json

import pytest

from app.domain.enums import PoolStatus
from app.repositories.demo_repository import DemoRepository
from app.services.intent_service import create_intent_and_join_pool


FORBIDDEN_CLAIMS = [
    "supplier confirmed",
    "payment completed",
    "real order created",
    "real eSIM provisioned",
    "real users joined",
]


def _fresh_repo() -> DemoRepository:
    return DemoRepository()


def test_headphones_input_joins_required_pool() -> None:
    repo = _fresh_repo()

    result = create_intent_and_join_pool(
        input_text="wireless headphones",
        city="Almaty",
        esim_profile_id="demo-esim-profile",
        repository=repo,
        user_language="en",
    )

    assert result["matchedExistingPool"] is True
    assert result["pool"] is not None
    assert result["pool"].id == "pool-almaty-headphones"


def test_headphones_join_increments_count_24_to_25() -> None:
    repo = _fresh_repo()

    create_intent_and_join_pool(
        "wireless headphones",
        "Almaty",
        "demo-esim-profile",
        repo,
        user_language="en",
    )

    pool = repo.get_pool("pool-almaty-headphones")
    assert pool is not None
    assert pool.current_intent_count == 25
    assert pool.missing_to_moq == 0


def test_headphones_join_triggers_deal_formed_true() -> None:
    repo = _fresh_repo()

    result = create_intent_and_join_pool(
        "wireless headphones",
        "Almaty",
        "demo-esim-profile",
        repo,
        user_language="en",
    )

    assert result["dealFormed"] is True


def test_deal_banner_appears_with_exact_copy() -> None:
    repo = _fresh_repo()

    result = create_intent_and_join_pool(
        "wireless headphones",
        "Almaty",
        "demo-esim-profile",
        repo,
        user_language="en",
    )

    assert result["dealBanner"] == {
        "title": "Pool reached 25 participants.",
        "message": "Birge formed a group deal.",
        "estimatedGroupPriceKzt": 14500,
        "estimatedSavingsPercent": 34,
    }


def test_updated_pool_status_becomes_deal_formed() -> None:
    repo = _fresh_repo()

    create_intent_and_join_pool(
        "wireless headphones",
        "Almaty",
        "demo-esim-profile",
        repo,
        user_language="en",
    )

    pool = repo.get_pool("pool-almaty-headphones")
    assert pool is not None
    assert pool.status == PoolStatus.deal_formed


def test_intent_record_is_attached_to_esim_profile_id() -> None:
    repo = _fresh_repo()

    create_intent_and_join_pool(
        "wireless headphones",
        "Almaty",
        "demo-esim-profile",
        repo,
        user_language="en",
    )

    stored = repo.list_user_intents("demo-esim-profile")
    assert len(stored) == 1


def test_stored_profile_intent_has_required_pool_id() -> None:
    repo = _fresh_repo()

    create_intent_and_join_pool(
        "wireless headphones",
        "Almaty",
        "demo-esim-profile",
        repo,
        user_language="en",
    )

    stored = repo.list_user_intents("demo-esim-profile")
    assert stored[0].pool_id == "pool-almaty-headphones"


def test_stored_profile_intent_is_demo_data() -> None:
    repo = _fresh_repo()

    create_intent_and_join_pool(
        "wireless headphones",
        "Almaty",
        "demo-esim-profile",
        repo,
        user_language="en",
    )

    stored = repo.list_user_intents("demo-esim-profile")
    assert stored[0].is_demo_data is True


def test_missing_esim_profile_id_raises_value_error() -> None:
    repo = _fresh_repo()

    with pytest.raises(ValueError):
        create_intent_and_join_pool("wireless headphones", "Almaty", " ", repo)


def test_empty_input_text_raises_value_error() -> None:
    repo = _fresh_repo()

    with pytest.raises(ValueError):
        create_intent_and_join_pool(" ", "Almaty", "demo-esim-profile", repo)


def test_empty_city_raises_value_error() -> None:
    repo = _fresh_repo()

    with pytest.raises(ValueError):
        create_intent_and_join_pool("wireless headphones", " ", "demo-esim-profile", repo)


def test_weird_unmatched_input_returns_no_pool_and_no_banner() -> None:
    repo = _fresh_repo()

    result = create_intent_and_join_pool(
        "ceramic moon wrench for balcony jazz",
        "Almaty",
        "demo-esim-profile",
        repo,
        user_language="en",
    )

    assert result["matchedExistingPool"] is False
    assert result["pool"] is None
    assert result["dealFormed"] is False
    assert result["dealBanner"] is None


def test_unmatched_input_does_not_create_new_pool() -> None:
    repo = _fresh_repo()
    original_pool_ids = set(repo.pools)

    create_intent_and_join_pool(
        "ceramic moon wrench for balcony jazz",
        "Almaty",
        "demo-esim-profile",
        repo,
        user_language="en",
    )

    assert set(repo.pools) == original_pool_ids


def test_response_text_does_not_make_forbidden_demo_claims() -> None:
    repo = _fresh_repo()

    result = create_intent_and_join_pool(
        "wireless headphones",
        "Almaty",
        "demo-esim-profile",
        repo,
        user_language="en",
    )
    response_text = json.dumps(result, default=str).lower()

    for claim in FORBIDDEN_CLAIMS:
        assert claim.lower() not in response_text


def test_intent_service_phase7_health_route_remains_available() -> None:
    from app.main import app

    routes = sorted(route.path for route in app.routes)
    assert "/health" in routes
