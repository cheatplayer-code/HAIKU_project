"""Tests for pricing service."""

import pytest

from app.domain.enums import IntentCategory
from app.services.pricing import (
    get_category_savings_benchmark,
    estimate_savings_percent,
    estimate_group_price_kzt,
    estimate_landed_cost,
)


class TestGetCategorySavingsBenchmark:
    """Tests for get_category_savings_benchmark function."""

    def test_electronics_benchmark_returns_min_28_max_36(self):
        """Electronics benchmark returns min=28, max=36."""
        result = get_category_savings_benchmark(IntentCategory.electronics)
        assert result.min == 28
        assert result.max == 36

    def test_all_categories_have_benchmark_coverage(self):
        """All IntentCategory values have benchmark coverage."""
        for category in IntentCategory:
            benchmark = get_category_savings_benchmark(category)
            assert benchmark.min >= 0
            assert benchmark.max <= 100
            assert benchmark.min <= benchmark.max
            # Verify default is valid using estimate_savings_percent
            default = estimate_savings_percent(category)
            assert default >= benchmark.min
            assert default <= benchmark.max


class TestEstimateSavingsPercent:
    """Tests for estimate_savings_percent function."""

    def test_electronics_default_savings_is_34(self):
        """Electronics default savings estimate is 34."""
        result = estimate_savings_percent(IntentCategory.electronics)
        assert result == 34

    def test_all_categories_return_valid_percent(self):
        """All categories return valid percentage."""
        for category in IntentCategory:
            result = estimate_savings_percent(category)
            assert 0 <= result <= 100


class TestEstimateGroupPriceKzt:
    """Tests for estimate_group_price_kzt function."""

    def test_electronics_22000_returns_rounded_expected_price(self):
        """estimate_group_price_kzt(22000, electronics) returns rounded expected price."""
        # 22000 * (1 - 34/100) = 22000 * 0.66 = 14520
        # Rounded to nearest 100 = 14500
        result = estimate_group_price_kzt(22000, IntentCategory.electronics)
        assert result == 14500

    def test_group_price_is_positive_and_le_retail(self):
        """Group price is positive and <= retail."""
        for category in IntentCategory:
            retail = 10000
            group_price = estimate_group_price_kzt(retail, category)
            assert group_price > 0
            assert group_price <= retail

    def test_invalid_retail_price_raises_value_error(self):
        """Invalid retail price raises ValueError."""
        with pytest.raises(ValueError, match="retail_price_kzt must be > 0"):
            estimate_group_price_kzt(0, IntentCategory.electronics)
        
        with pytest.raises(ValueError, match="retail_price_kzt must be > 0"):
            estimate_group_price_kzt(-100, IntentCategory.electronics)

    def test_rounding_to_nearest_100(self):
        """Group price is rounded to nearest 100 KZT."""
        # Test with a price that would give non-100 result
        result = estimate_group_price_kzt(10000, IntentCategory.books)
        # books default is 16%, so 10000 * 0.84 = 8400 (already at 100)
        assert result % 100 == 0


class TestEstimateLandedCost:
    """Tests for estimate_landed_cost function."""

    def test_landed_cost_total_equals_product_plus_cargo_plus_duty(self):
        """Landed cost total = product + cargo + duty."""
        product_price = 10000
        duty = 500
        result = estimate_landed_cost(product_price, IntentCategory.electronics, duty)
        
        # electronics cargo is 1800
        expected_total = product_price + 1800 + duty
        assert result.total_landed_cost_kzt == expected_total

    def test_landed_cost_note_says_demo_estimate_not_customs_accurate(self):
        """Landed cost note says demo estimate / not customs-accurate."""
        result = estimate_landed_cost(10000, IntentCategory.electronics)
        assert "DEMO ESTIMATE" in result.note
        assert "NOT customs-accurate" in result.note or "not customs-accurate" in result.note

    def test_zero_duty_default(self):
        """Duty defaults to 0 when not provided."""
        result = estimate_landed_cost(10000, IntentCategory.electronics)
        assert result.duty_estimate_kzt == 0

    def test_invalid_product_price_raises_value_error(self):
        """Invalid product price raises ValueError."""
        with pytest.raises(ValueError, match="product_price_kzt must be >= 0"):
            estimate_landed_cost(-1, IntentCategory.electronics)

    def test_invalid_duty_raises_value_error(self):
        """Invalid duty raises ValueError."""
        with pytest.raises(ValueError, match="duty_estimate_kzt must be >= 0"):
            estimate_landed_cost(10000, IntentCategory.electronics, -100)

    def test_all_categories_have_cargo_estimates(self):
        """All categories have cargo estimates."""
        for category in IntentCategory:
            result = estimate_landed_cost(10000, category)
            assert result.cargo_estimate_kzt > 0
            assert result.total_landed_cost_kzt > 0
