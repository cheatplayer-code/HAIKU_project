"""Intent join orchestration service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.domain.enums import PoolStatus
from app.domain.models import DemandPoolDto, ProfileIntent
from app.services.intent_parser import parse_intent
from app.services.pool_matcher import match_intent_to_pool

if TYPE_CHECKING:
    from app.repositories.demo_repository import DemoRepository


def _require_non_empty(value: str, field_name: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field_name} cannot be empty")
    return stripped


def _demo_intent_id(esim_profile_id: str, pool_id: str | None, next_index: int) -> str:
    readable_profile = "".join(
        char.lower() if char.isalnum() else "-" for char in esim_profile_id.strip()
    ).strip("-")
    pool_part = pool_id or "unmatched"
    return f"demo-intent-{readable_profile}-{pool_part}-{next_index}"


def create_intent_and_join_pool(
    input_text: str,
    city: str,
    esim_profile_id: str,
    repository: DemoRepository,
    user_language: str | None = None,
) -> dict[str, object]:
    """Parse an intent, match it to a demo pool, and store the joined intent."""
    input_text = _require_non_empty(input_text, "input_text")
    city = _require_non_empty(city, "city")
    esim_profile_id = _require_non_empty(esim_profile_id, "esim_profile_id")

    parsed_intent = parse_intent(
        input_text,
        user_language=user_language,
        prefer_cache=True,
    )
    candidate_pools = repository.list_pools(
        city=city,
        category=parsed_intent.category,
        limit=20,
    )
    match_result = match_intent_to_pool(parsed_intent, candidate_pools, city=city)

    next_index = len(repository.list_user_intents(esim_profile_id)) + 1
    intent_id = _demo_intent_id(esim_profile_id, match_result.pool.id if match_result.pool else None, next_index)

    if not match_result.matched_existing_pool or match_result.pool is None:
        return {
            "intentId": intent_id,
            "parsedIntent": parsed_intent,
            "matchedExistingPool": False,
            "pool": None,
            "dealFormed": False,
            "dealBanner": None,
            "isDemoData": True,
        }

    pool = match_result.pool
    new_count = pool.current_intent_count + 1
    new_missing_to_moq = max(pool.moq - new_count, 0)
    new_status = PoolStatus.deal_formed if new_count >= pool.moq else pool.status
    updated_pool_data = pool.model_dump()
    updated_pool_data.update(
        {
            "current_intent_count": new_count,
            "missing_to_moq": new_missing_to_moq,
            "status": new_status,
        }
    )
    updated_pool = DemandPoolDto.model_validate(updated_pool_data)
    repository.update_pool(updated_pool)

    profile_intent = ProfileIntent(
        id=intent_id,
        title=parsed_intent.normalized_title,
        localized_title=parsed_intent.localized_title,
        city=city,
        category=parsed_intent.category,
        pool_id=updated_pool.id,
        pool_status=updated_pool.status,
        created_at=datetime.now(timezone.utc).isoformat(),
        is_demo_data=True,
    )
    repository.add_user_intent(esim_profile_id, profile_intent)

    deal_formed = updated_pool.current_intent_count >= updated_pool.moq
    deal_banner = None
    if deal_formed:
        deal_banner = {
            "title": f"Pool reached {updated_pool.moq} participants.",
            "message": "Birge formed a group deal.",
            "estimatedGroupPriceKzt": updated_pool.estimated_group_price_kzt,
            "estimatedSavingsPercent": updated_pool.estimated_savings_percent,
        }

    return {
        "intentId": intent_id,
        "parsedIntent": parsed_intent,
        "matchedExistingPool": True,
        "pool": updated_pool,
        "dealFormed": deal_formed,
        "dealBanner": deal_banner,
        "isDemoData": True,
    }
