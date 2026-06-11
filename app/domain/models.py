"""Birge domain models."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

from app.domain.enums import InputType, IntentCategory, ParserMode, PoolStatus, SupportedLanguage


class ParsedIntent(BaseModel):
    """Parsed buying intent from URL or text input."""

    input_type: InputType
    source_text: str = Field(..., min_length=1)
    normalized_title: str = Field(..., min_length=1)
    localized_title: str = Field(..., min_length=1)
    language: SupportedLanguage
    category: IntentCategory
    specs: dict[str, str | int | float | bool] = Field(default_factory=dict)
    estimated_unit_price_kzt: int | None = None
    budget_min_kzt: int | None = None
    budget_max_kzt: int | None = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    parser_mode: ParserMode
    explanation: str

    @field_validator("estimated_unit_price_kzt", "budget_min_kzt", "budget_max_kzt")
    @classmethod
    def _check_non_negative_prices(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("Price/budget values cannot be negative")
        return v

    @model_validator(mode="after")
    def _check_budget_range(self) -> ParsedIntent:
        if self.budget_min_kzt is not None and self.budget_max_kzt is not None:
            if self.budget_min_kzt > self.budget_max_kzt:
                raise ValueError("budget_min_kzt must be <= budget_max_kzt")
        return self


class SavingsIntervalPercent(BaseModel):
    """Savings percentage interval."""

    min: int = Field(..., ge=0)
    max: int = Field(..., le=100)

    @model_validator(mode="after")
    def _check_interval(self) -> SavingsIntervalPercent:
        if self.min > self.max:
            raise ValueError("min must be <= max")
        return self


class DemandPoolDto(BaseModel):
    """Demand pool data transfer object."""

    id: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1)
    category: IntentCategory
    title: str = Field(..., min_length=1)
    localized_title: str = Field(..., min_length=1)
    status: PoolStatus
    current_intent_count: int = Field(..., ge=0)
    moq: int = Field(..., gt=0)
    missing_to_moq: int = Field(..., ge=0)
    estimated_retail_price_kzt: int = Field(..., gt=0)
    estimated_group_price_kzt: int = Field(..., gt=0)
    estimated_savings_percent: int = Field(..., ge=0, le=100)
    savings_interval_percent: SavingsIntervalPercent
    benchmark_source: str = "demo_category_benchmark"
    is_demo_data: bool = True

    @model_validator(mode="after")
    def _validate_pool(self) -> DemandPoolDto:
        if self.estimated_group_price_kzt > self.estimated_retail_price_kzt:
            raise ValueError(
                "estimated_group_price_kzt must be <= estimated_retail_price_kzt"
            )
        expected_missing = max(self.moq - self.current_intent_count, 0)
        if self.missing_to_moq != expected_missing:
            raise ValueError(
                f"missing_to_moq should be {expected_missing}, got {self.missing_to_moq}"
            )
        return self

    @classmethod
    def from_counts(
        cls,
        id: str,
        city: str,
        category: IntentCategory,
        title: str,
        localized_title: str,
        status: PoolStatus,
        current_intent_count: int,
        moq: int,
        estimated_retail_price_kzt: int,
        estimated_savings_percent: int,
        savings_interval_percent: SavingsIntervalPercent,
        benchmark_source: str = "demo_category_benchmark",
        is_demo_data: bool = True,
    ) -> DemandPoolDto:
        """Create a DemandPoolDto from counts, computing derived fields."""
        missing_to_moq = max(moq - current_intent_count, 0)
        estimated_group_price_kzt = int(
            round(estimated_retail_price_kzt * (1 - estimated_savings_percent / 100), -2)
        )
        return cls(
            id=id,
            city=city,
            category=category,
            title=title,
            localized_title=localized_title,
            status=status,
            current_intent_count=current_intent_count,
            moq=moq,
            missing_to_moq=missing_to_moq,
            estimated_retail_price_kzt=estimated_retail_price_kzt,
            estimated_group_price_kzt=estimated_group_price_kzt,
            estimated_savings_percent=estimated_savings_percent,
            savings_interval_percent=savings_interval_percent,
            benchmark_source=benchmark_source,
            is_demo_data=is_demo_data,
        )


class PoolMatchRuleChecks(BaseModel):
    """Rule checks for pool matching."""

    city_matched: bool
    category_matched: bool
    budget_overlapped: bool
    similarity_passed: bool


class PoolMatchResult(BaseModel):
    """Result of pool matching operation."""

    matched_existing_pool: bool
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    rule_checks: PoolMatchRuleChecks
    pool: DemandPoolDto | None = None

    @model_validator(mode="after")
    def _check_pool_required(self) -> PoolMatchResult:
        if self.matched_existing_pool and self.pool is None:
            raise ValueError("pool must not be None when matched_existing_pool is True")
        return self


class LandedCostBreakdown(BaseModel):
    """Landed cost breakdown estimate."""

    product_price_kzt: int = Field(..., ge=0)
    cargo_estimate_kzt: int = Field(..., ge=0)
    duty_estimate_kzt: int = Field(..., ge=0)
    total_landed_cost_kzt: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def _check_total(self) -> LandedCostBreakdown:
        expected_total = (
            self.product_price_kzt + self.cargo_estimate_kzt + self.duty_estimate_kzt
        )
        if self.total_landed_cost_kzt != expected_total:
            raise ValueError(
                f"total_landed_cost_kzt must equal sum of components ({expected_total})"
            )
        return self


class CityDemandPoint(BaseModel):
    """City demand point for visualization."""

    lat: float = Field(..., ge=-90.0, le=90.0)
    lng: float = Field(..., ge=-180.0, le=180.0)
    weight: float = Field(..., ge=0.0, le=1.0)
    is_synthetic_demo_point: bool = True


class TimelineStep(BaseModel):
    """Timeline step for pool progress."""

    step: str = Field(..., min_length=1)
    status: str

    @field_validator("status")
    @classmethod
    def _check_status(cls, v: str) -> str:
        allowed = {"done", "current", "upcoming"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class ProfileIntent(BaseModel):
    """User profile intent record."""

    id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    localized_title: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1)
    category: IntentCategory
    pool_id: str | None = None
    pool_status: PoolStatus | None = None
    created_at: str = Field(..., min_length=1)
    is_demo_data: bool = True
