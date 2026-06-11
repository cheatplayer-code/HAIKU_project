"""FastAPI routes for the Birge demo intelligence layer."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.dependencies import get_demo_repository
from app.api.schemas import CreateIntentRequest, MatchPoolRequest, ParseIntentRequest
from app.domain.enums import IntentCategory, PoolStatus
from app.domain.models import ParsedIntent
from app.repositories.demo_repository import DemoRepository
from app.services.intent_parser import parse_intent
from app.services.intent_service import create_intent_and_join_pool
from app.services.pool_matcher import match_intent_to_pool
from app.services.pricing import estimate_landed_cost


router = APIRouter()


def _snake_to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


def _camel_to_snake(value: str) -> str:
    output = []
    for char in value:
        if char.isupper():
            output.append("_")
            output.append(char.lower())
        else:
            output.append(char)
    return "".join(output).lstrip("_")


def _to_api(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _to_api(value.model_dump(mode="json"))
    if isinstance(value, list):
        return [_to_api(item) for item in value]
    if isinstance(value, dict):
        return {
            _snake_to_camel(str(key)): _to_api(item)
            for key, item in value.items()
        }
    return value


def _to_domain(value: Any) -> Any:
    if isinstance(value, list):
        return [_to_domain(item) for item in value]
    if isinstance(value, dict):
        return {
            _camel_to_snake(str(key)): _to_domain(item)
            for key, item in value.items()
        }
    return value


def _success(
    data: dict[str, Any],
    parser_mode: str | None = None,
    status_code: int = status.HTTP_200_OK,
) -> JSONResponse:
    meta: dict[str, Any] = {"isDemoData": True}
    if parser_mode is not None:
        meta["parserMode"] = parser_mode
    return JSONResponse(
        status_code=status_code,
        content={
            "ok": True,
            "data": _to_api(data),
            "meta": meta,
        },
    )


def _error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "ok": False,
            "error": {
                "code": code,
                "message": message,
                "details": None,
            },
        },
    )


@router.post("/api/intent/parse")
def parse_intent_endpoint(request: ParseIntentRequest) -> JSONResponse:
    """Parse a product URL or free-text buying intent."""
    try:
        parsed = parse_intent(
            request.input,
            user_language=request.user_language,
            prefer_cache=True,
        )
    except ValueError as exc:
        return _error(status.HTTP_400_BAD_REQUEST, "invalid_intent_input", str(exc))

    return _success(
        {"intent": parsed},
        parser_mode=parsed.parser_mode.value,
    )


@router.post("/api/pools/match")
def match_pool_endpoint(
    request: MatchPoolRequest,
    repository: DemoRepository = Depends(get_demo_repository),
) -> JSONResponse:
    """Match a parsed intent to an existing city-level pool."""
    try:
        parsed_intent = ParsedIntent.model_validate(_to_domain(request.intent))
    except ValueError as exc:
        return _error(status.HTTP_400_BAD_REQUEST, "invalid_parsed_intent", str(exc))

    candidate_pools = repository.list_pools(
        city=request.city,
        category=parsed_intent.category,
        limit=20,
    )
    match_result = match_intent_to_pool(
        parsed_intent,
        candidate_pools,
        city=request.city,
    )
    return _success(
        {
            "match": {
                "matched_existing_pool": match_result.matched_existing_pool,
                "similarity_score": match_result.similarity_score,
                "rule_checks": match_result.rule_checks,
                "pool": match_result.pool,
            }
        },
        parser_mode=parsed_intent.parser_mode.value,
    )


@router.post("/api/intents")
def create_intent_endpoint(
    request: CreateIntentRequest,
    repository: DemoRepository = Depends(get_demo_repository),
) -> JSONResponse:
    """Create an intent and join a matching demo pool."""
    try:
        result = create_intent_and_join_pool(
            input_text=request.input,
            city=request.city,
            esim_profile_id=request.esim_profile_id,
            repository=repository,
            user_language=request.user_language,
        )
    except ValueError as exc:
        return _error(status.HTTP_400_BAD_REQUEST, "invalid_create_intent_request", str(exc))

    parsed_intent = result["parsedIntent"]
    parser_mode = (
        parsed_intent.parser_mode.value
        if isinstance(parsed_intent, ParsedIntent)
        else None
    )
    return _success(result, parser_mode=parser_mode)


@router.get("/api/pools")
def list_pools_endpoint(
    city: str = "Almaty",
    category: IntentCategory | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    repository: DemoRepository = Depends(get_demo_repository),
) -> JSONResponse:
    """Return city demand pulse pools."""
    pools = repository.list_pools(city=city, category=category, limit=limit)
    total_forming = sum(1 for pool in pools if pool.status == PoolStatus.forming)
    return _success(
        {
            "city": city,
            "total_forming_pools": total_forming,
            "pools": pools,
        },
    )


@router.get("/api/pools/{pool_id}")
def get_pool_endpoint(
    pool_id: str,
    repository: DemoRepository = Depends(get_demo_repository),
) -> JSONResponse:
    """Return detailed pool data."""
    pool = repository.get_pool(pool_id)
    if pool is None:
        return _error(status.HTTP_404_NOT_FOUND, "pool_not_found", "Pool not found")

    landed_cost = estimate_landed_cost(
        product_price_kzt=pool.estimated_group_price_kzt,
        category=pool.category,
    )
    timeline = [
        {"step": "demand_collection", "status": "done"},
        {
            "step": "moq_reached",
            "status": "done" if pool.current_intent_count >= pool.moq else "current",
        },
        {
            "step": "group_deal_formed",
            "status": "done" if pool.status == PoolStatus.deal_formed else "upcoming",
        },
        {"step": "buyout", "status": "upcoming"},
        {"step": "delivery", "status": "upcoming"},
    ]
    city_demand_points = [
        {
            "lat": 43.2389,
            "lng": 76.8897,
            "weight": 0.9,
            "is_synthetic_demo_point": True,
        },
        {
            "lat": 43.2567,
            "lng": 76.9286,
            "weight": 0.7,
            "is_synthetic_demo_point": True,
        },
        {
            "lat": 43.2220,
            "lng": 76.8512,
            "weight": 0.5,
            "is_synthetic_demo_point": True,
        },
    ]
    pool_detail = pool.model_dump(mode="json")
    pool_detail.update(
        {
            "landed_cost_breakdown": landed_cost,
            "timeline": timeline,
            "city_demand_points": city_demand_points,
        }
    )
    return _success({"pool": pool_detail})


@router.get("/api/profile/intents")
def get_profile_intents_endpoint(
    esim_profile_id: str = Query(..., alias="esimProfileId"),
    repository: DemoRepository = Depends(get_demo_repository),
) -> JSONResponse:
    """Return stored profile intents for a demo eSIM identity profile."""
    intents = repository.list_user_intents(esim_profile_id)
    return _success(
        {
            "esim_profile_id": esim_profile_id,
            "intents": intents,
        },
    )
