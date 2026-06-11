"""Rule-based pricing helpers for demo purposes."""

from app.domain.enums import IntentCategory
from app.domain.models import SavingsIntervalPercent, LandedCostBreakdown


# Benchmark savings percentages by category
# Format: {category: (min, max, default)}
_CATEGORY_BENCHMARKS: dict[IntentCategory, tuple[int, int, int]] = {
    IntentCategory.electronics: (28, 36, 34),
    IntentCategory.home: (30, 42, 38),
    IntentCategory.fashion: (20, 35, 29),
    IntentCategory.beauty: (18, 30, 24),
    IntentCategory.sports: (22, 34, 28),
    IntentCategory.kids: (20, 32, 26),
    IntentCategory.auto: (15, 28, 21),
    IntentCategory.books: (10, 22, 16),
    IntentCategory.other: (12, 25, 18),
}

# Demo cargo estimates by category (in KZT)
_CARGO_ESTIMATES: dict[IntentCategory, int] = {
    IntentCategory.electronics: 1800,
    IntentCategory.home: 2500,
    IntentCategory.fashion: 1200,
    IntentCategory.beauty: 1000,
    IntentCategory.sports: 1800,
    IntentCategory.kids: 1500,
    IntentCategory.auto: 2200,
    IntentCategory.books: 900,
    IntentCategory.other: 1500,
}


def get_category_savings_benchmark(category: IntentCategory) -> SavingsIntervalPercent:
    """Get the savings interval benchmark for a category.
    
    Args:
        category: The intent category.
        
    Returns:
        SavingsIntervalPercent with min, max values.
        
    Raises:
        ValueError: If category is not recognized.
    """
    if category not in _CATEGORY_BENCHMARKS:
        raise ValueError(f"Unknown category: {category}")
    
    min_val, max_val, _ = _CATEGORY_BENCHMARKS[category]
    return SavingsIntervalPercent(min=min_val, max=max_val)


def _get_default_savings_percent(category: IntentCategory) -> int:
    """Get the default savings percentage for a category."""
    if category not in _CATEGORY_BENCHMARKS:
        raise ValueError(f"Unknown category: {category}")
    return _CATEGORY_BENCHMARKS[category][2]


def estimate_savings_percent(category: IntentCategory) -> int:
    """Estimate the default savings percentage for a category.
    
    Args:
        category: The intent category.
        
    Returns:
        Default savings percentage as an integer.
    """
    return _get_default_savings_percent(category)


def estimate_group_price_kzt(retail_price_kzt: int, category: IntentCategory) -> int:
    """Estimate the group purchase price based on retail price and category.
    
    Args:
        retail_price_kzt: The estimated retail price in KZT. Must be > 0.
        category: The intent category.
        
    Returns:
        Estimated group price in KZT, rounded to nearest 100.
        
    Raises:
        ValueError: If retail_price_kzt is not positive.
    """
    if retail_price_kzt <= 0:
        raise ValueError("retail_price_kzt must be > 0")
    
    savings_percent = estimate_savings_percent(category)
    group_price = retail_price_kzt * (1 - savings_percent / 100)
    
    # Round to nearest 100 KZT
    group_price_rounded = round(group_price / 100) * 100
    
    # Ensure group price is positive and <= retail
    if group_price_rounded <= 0:
        group_price_rounded = 100  # Minimum positive value
    if group_price_rounded > retail_price_kzt:
        group_price_rounded = retail_price_kzt
    
    return group_price_rounded


def estimate_landed_cost(
    product_price_kzt: int,
    category: IntentCategory,
    duty_estimate_kzt: int = 0,
) -> LandedCostBreakdown:
    """Estimate the landed cost including product, cargo, and duty.
    
    Args:
        product_price_kzt: The product price in KZT. Must be >= 0.
        category: The intent category.
        duty_estimate_kzt: Estimated duty in KZT. Must be >= 0. Defaults to 0.
        
    Returns:
        LandedCostBreakdown with product, cargo, duty, total, and note.
        
    Raises:
        ValueError: If product_price_kzt or duty_estimate_kzt is negative.
    """
    if product_price_kzt < 0:
        raise ValueError("product_price_kzt must be >= 0")
    if duty_estimate_kzt < 0:
        raise ValueError("duty_estimate_kzt must be >= 0")
    
    cargo_estimate = _CARGO_ESTIMATES.get(category, _CARGO_ESTIMATES[IntentCategory.other])
    total = product_price_kzt + cargo_estimate + duty_estimate_kzt
    
    note = "DEMO ESTIMATE ONLY: This is a simplified demo calculation and NOT customs-accurate. Actual logistics costs may vary significantly."
    
    return LandedCostBreakdown(
        product_price_kzt=product_price_kzt,
        cargo_estimate_kzt=cargo_estimate,
        duty_estimate_kzt=duty_estimate_kzt,
        total_landed_cost_kzt=total,
        note=note,
    )
