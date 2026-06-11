"""Pool matching service for Birge demand aggregation."""

from __future__ import annotations

import re

from app.domain.enums import IntentCategory, PoolStatus
from app.domain.models import DemandPoolDto, ParsedIntent, PoolMatchResult, PoolMatchRuleChecks


# Stopwords for keyword similarity calculation
STOPWORDS = {
    # English
    "the", "a", "an", "i", "want", "need", "cheap", "do", "for",
    # Russian
    "хочу", "нужен", "нужна", "нужно", "до", "для",
    # Kazakh
    "керек", "маған", "саған", "оған", "бізге",
}


def _normalize_text(text: str) -> set[str]:
    """Normalize text: lowercase, remove punctuation, split tokens, remove stopwords."""
    # Lowercase
    text_lower = text.lower()
    # Remove punctuation (keep alphanumeric and spaces)
    text_clean = re.sub(r"[^\w\s]", " ", text_lower)
    # Split into tokens
    tokens = text_clean.split()
    # Remove stopwords and short tokens
    return {t for t in tokens if t not in STOPWORDS and len(t) > 1}


def calculate_keyword_similarity(intent: ParsedIntent, pool: DemandPoolDto) -> float:
    """Calculate keyword similarity between intent and pool.
    
    Uses deterministic token overlap between:
    - intent.normalized_title
    - intent.localized_title
    - pool.title
    - pool.localized_title
    
    Args:
        intent: The parsed intent to match.
        pool: The demand pool to match against.
    
    Returns:
        Float between 0 and 1 representing similarity score.
    """
    # Collect all text from intent
    intent_texts = [
        intent.normalized_title,
        intent.localized_title,
    ]
    
    # Add specs string values if present
    for key, value in intent.specs.items():
        if isinstance(value, str):
            intent_texts.append(value)
    
    # Collect all text from pool
    pool_texts = [
        pool.title,
        pool.localized_title,
    ]
    
    # Normalize all texts
    intent_tokens: set[str] = set()
    for text in intent_texts:
        intent_tokens.update(_normalize_text(text))
    
    pool_tokens: set[str] = set()
    for text in pool_texts:
        pool_tokens.update(_normalize_text(text))
    
    # Calculate Jaccard similarity
    if not intent_tokens or not pool_tokens:
        return 0.0
    
    intersection = intent_tokens & pool_tokens
    union = intent_tokens | pool_tokens
    
    if not union:
        return 0.0
    
    similarity = len(intersection) / len(union)
    
    # Clamp to [0, 1]
    return max(0.0, min(1.0, similarity))


def budget_overlaps_intent_pool(intent: ParsedIntent, pool: DemandPoolDto) -> bool:
    """Check if intent budget overlaps with pool's estimated group price.
    
    Rules:
    - If no budget info exists, return True.
    - If intent.budget_max_kzt exists, return True when:
      intent.budget_max_kzt >= pool.estimated_group_price_kzt * 0.8
    - If intent.budget_min_kzt exists, do not reject cheaper group deals.
    
    Args:
        intent: The parsed intent with budget info.
        pool: The demand pool with estimated group price.
    
    Returns:
        True if budget overlaps, False otherwise.
    """
    # If no budget info, allow matching
    if intent.budget_max_kzt is None and intent.budget_min_kzt is None:
        return True
    
    # Check budget_max constraint
    if intent.budget_max_kzt is not None:
        # Allow if max budget is at least 80% of group price
        threshold = pool.estimated_group_price_kzt * 0.8
        if intent.budget_max_kzt < threshold:
            return False
    
    # budget_min does not reject cheaper deals
    return True


def match_intent_to_pool(
    intent: ParsedIntent,
    candidate_pools: list[DemandPoolDto],
    city: str,
    similarity_threshold: float = 0.45,
) -> PoolMatchResult:
    """Match an intent to the best existing pool.
    
    Rules:
    - City must match case-insensitively.
    - Category must match.
    - If intent.category is "other", do not match specific pools unless pool.category is also "other".
    - Only match pools with status: forming, ready.
    - Do NOT match: deal_formed, closed.
    - Budget must overlap.
    - Similarity must be >= threshold.
    - Choose best matching pool by:
      1. highest similarity_score
      2. higher current_intent_count
      3. lower missing_to_moq
      4. stable deterministic ordering by id
    
    Args:
        intent: The parsed intent to match.
        candidate_pools: List of candidate pools to consider.
        city: The city to filter by (case-insensitive).
        similarity_threshold: Minimum similarity score to consider a match.
    
    Returns:
        PoolMatchResult with matched pool or None.
    """
    # Filter pools by city (case-insensitive)
    city_matched_pools = [
        p for p in candidate_pools
        if p.city.lower() == city.lower()
    ]
    
    # Track rule checks for the best match
    best_match: tuple[float, DemandPoolDto] | None = None
    
    for pool in city_matched_pools:
        # Check category match
        category_matched = (
            intent.category == pool.category or
            (intent.category == IntentCategory.other and pool.category == IntentCategory.other)
        )
        if not category_matched:
            continue
        
        # Check pool status
        if pool.status not in (PoolStatus.forming, PoolStatus.ready):
            continue
        
        # Check budget overlap
        budget_overlapped = budget_overlaps_intent_pool(intent, pool)
        if not budget_overlapped:
            continue
        
        # Calculate similarity
        similarity = calculate_keyword_similarity(intent, pool)
        
        # Check similarity threshold
        if similarity < similarity_threshold:
            continue
        
        # This pool passes all filters - check if it's the best match
        # Sort key: (-similarity, -current_intent_count, missing_to_moq, id)
        match_key = (
            -similarity,
            -pool.current_intent_count,
            pool.missing_to_moq,
            pool.id,
        )
        
        if best_match is None:
            best_match = (similarity, pool)
        else:
            current_key = (
                -best_match[0],
                -best_match[1].current_intent_count,
                best_match[1].missing_to_moq,
                best_match[1].id,
            )
            if match_key < current_key:
                best_match = (similarity, pool)
    
    # No match found
    if best_match is None:
        # Return result with similarity 0 and all rule checks False
        return PoolMatchResult(
            matched_existing_pool=False,
            similarity_score=0.0,
            rule_checks=PoolMatchRuleChecks(
                city_matched=len(city_matched_pools) > 0,
                category_matched=False,
                budget_overlapped=False,
                similarity_passed=False,
            ),
            pool=None,
        )
    
    similarity, pool = best_match
    
    return PoolMatchResult(
        matched_existing_pool=True,
        similarity_score=similarity,
        rule_checks=PoolMatchRuleChecks(
            city_matched=True,
            category_matched=True,
            budget_overlapped=True,
            similarity_passed=similarity >= similarity_threshold,
        ),
        pool=pool,
    )
