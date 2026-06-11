"""Simple API request schemas."""

from typing import Any

from pydantic import BaseModel, ConfigDict


def _snake_to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


class _ApiRequest(BaseModel):
    model_config = ConfigDict(
        alias_generator=_snake_to_camel,
        populate_by_name=True,
    )


class ParseIntentRequest(_ApiRequest):
    """Request body for intent parsing."""

    input: str
    city: str
    user_language: str | None = None


class MatchPoolRequest(_ApiRequest):
    """Request body for pool matching."""

    city: str
    intent: dict[str, Any]


class CreateIntentRequest(_ApiRequest):
    """Request body for creating and joining an intent."""

    city: str
    esim_profile_id: str
    input: str
    user_language: str | None = None
