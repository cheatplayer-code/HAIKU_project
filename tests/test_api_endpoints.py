"""API endpoint tests for the Birge demo intelligence layer."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import reset_demo_repository
from app.main import app


client = TestClient(app)

FORBIDDEN_CLAIMS = [
    "supplier confirmed",
    "payment completed",
    "real order created",
    "real eSIM provisioned",
    "real users joined",
]


@pytest.fixture(autouse=True)
def reset_repository() -> None:
    reset_demo_repository()


def test_health_still_returns_200() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_parse_intent_returns_ok_and_data_intent() -> None:
    response = client.post(
        "/api/intent/parse",
        json={"input": "wireless headphones", "city": "Almaty", "userLanguage": "en"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["ok"] is True
    assert "intent" in body["data"]


def test_parse_headphones_url_returns_cache_fallback_parser_mode() -> None:
    response = client.post(
        "/api/intent/parse",
        json={
            "input": "https://example.com/headphones-demo",
            "city": "Almaty",
            "userLanguage": "en",
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["meta"]["parserMode"] == "cache_fallback"


def test_match_pool_matches_headphones_intent_to_required_pool() -> None:
    parse_response = client.post(
        "/api/intent/parse",
        json={"input": "wireless headphones", "city": "Almaty", "userLanguage": "en"},
    )
    intent = parse_response.json()["data"]["intent"]

    response = client.post(
        "/api/pools/match",
        json={"city": "Almaty", "intent": intent},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["ok"] is True
    assert body["data"]["match"]["matchedExistingPool"] is True
    assert body["data"]["match"]["pool"]["id"] == "pool-almaty-headphones"


def test_list_pools_city_returns_only_almaty_pools() -> None:
    response = client.get("/api/pools?city=Almaty")

    body = response.json()
    assert response.status_code == 200
    assert body["ok"] is True
    assert body["data"]["pools"]
    for pool in body["data"]["pools"]:
        assert pool["city"] == "Almaty"


def test_list_pools_filters_category() -> None:
    response = client.get("/api/pools?city=Almaty&category=electronics")

    body = response.json()
    assert response.status_code == 200
    assert body["data"]["pools"]
    for pool in body["data"]["pools"]:
        assert pool["category"] == "electronics"


def test_get_pool_detail_returns_required_pool() -> None:
    response = client.get("/api/pools/pool-almaty-headphones")

    body = response.json()
    assert response.status_code == 200
    assert body["ok"] is True
    assert body["data"]["pool"]["id"] == "pool-almaty-headphones"
    assert "landedCostBreakdown" in body["data"]["pool"]
    assert "timeline" in body["data"]["pool"]
    assert body["data"]["pool"]["cityDemandPoints"][0]["isSyntheticDemoPoint"] is True


def test_get_missing_pool_returns_structured_404() -> None:
    response = client.get("/api/pools/missing-pool")

    body = response.json()
    assert response.status_code == 404
    assert body == {
        "ok": False,
        "error": {
            "code": "pool_not_found",
            "message": "Pool not found",
            "details": None,
        },
    }


def test_create_intent_headphones_triggers_24_to_25_and_deal_formed() -> None:
    response = client.post(
        "/api/intents",
        json={
            "city": "Almaty",
            "esimProfileId": "demo-esim-profile",
            "input": "wireless headphones",
            "userLanguage": "en",
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["ok"] is True
    assert body["data"]["pool"]["currentIntentCount"] == 25
    assert body["data"]["dealFormed"] is True
    assert body["data"]["dealBanner"] is not None


def test_create_intent_empty_esim_profile_id_returns_structured_400() -> None:
    response = client.post(
        "/api/intents",
        json={
            "city": "Almaty",
            "esimProfileId": " ",
            "input": "wireless headphones",
            "userLanguage": "en",
        },
    )

    body = response.json()
    assert response.status_code == 400
    assert body["ok"] is False
    assert body["error"]["code"] == "invalid_create_intent_request"


def test_get_profile_intents_returns_stored_intent_after_post() -> None:
    client.post(
        "/api/intents",
        json={
            "city": "Almaty",
            "esimProfileId": "demo-esim-profile",
            "input": "wireless headphones",
            "userLanguage": "en",
        },
    )

    response = client.get("/api/profile/intents?esimProfileId=demo-esim-profile")

    body = response.json()
    assert response.status_code == 200
    assert body["ok"] is True
    assert body["data"]["esimProfileId"] == "demo-esim-profile"
    assert len(body["data"]["intents"]) == 1
    assert body["data"]["intents"][0]["poolId"] == "pool-almaty-headphones"


def test_api_responses_do_not_make_forbidden_demo_claims() -> None:
    responses = [
        client.post(
            "/api/intents",
            json={
                "city": "Almaty",
                "esimProfileId": "demo-esim-profile",
                "input": "wireless headphones",
                "userLanguage": "en",
            },
        ),
        client.get("/api/pools/pool-almaty-headphones"),
        client.get("/api/profile/intents?esimProfileId=demo-esim-profile"),
    ]
    response_text = json.dumps([response.json() for response in responses]).lower()

    for claim in FORBIDDEN_CLAIMS:
        assert claim.lower() not in response_text


def test_all_expected_api_routes_exist() -> None:
    routes = sorted(route.path for route in app.routes)

    assert "/health" in routes
    assert "/api/intent/parse" in routes
    assert "/api/pools/match" in routes
    assert "/api/intents" in routes
    assert "/api/pools" in routes
    assert "/api/pools/{pool_id}" in routes
    assert "/api/profile/intents" in routes
