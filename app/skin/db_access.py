# =============================================================================
# db_access.py  —  Database Access Layer
#
# This file is the bridge between the database and logic.py / masks.py / goals.py.
#
# Every function:
#   1. Checks the Django cache first
#   2. If cache empty — loads from database
#   3. Stores result in cache for 1 hour
#   4. Returns data in the SAME FORMAT as the original Python dicts
#
# When admin saves a record, admin.py calls cache.delete(key) to force
# fresh data on the next request. No stale data reaches the engine.
#
# Cache keys:
#   ingredient_db, concern_timelines, conflict_pairs, avoid_map,
#   plain_text_keywords, next_goals, mask_db, goals_db, product_db
# =============================================================================

from django.core.cache import cache

from .models import (
    Ingredient, ConcernTimeline, ConflictPair, AvoidIngredient,
    PlainTextKeyword, NextGoal, FaceMask, SkinGoal, Product,
)


def get_ingredient_db():
    """
    Returns INGREDIENT_DB format dict from database.
    {
        "niacinamide": {
            "label": "Niacinamide 5%",
            "targets": ["acne", "oiliness", ...],
            "why": "...",
            "sensitivity_safe": True,
            "dehydrated_safe": True,
            "phase_min": 2,
            "product_type": "serum",
            "time": "AM/PM",
        },
        ...
    }
    """
    cached = cache.get("ingredient_db")
    if cached is not None:
        return cached

    result = {}

    for ingredient in Ingredient.objects.filter(is_active=True):
        result[ingredient.key] = {
            "label":            ingredient.label,
            "why":              ingredient.why,
            "targets":          ingredient.get_targets_list(),
            "sensitivity_safe": ingredient.sensitivity_safe,
            "dehydrated_safe":  ingredient.dehydrated_safe,
            "phase_min":        ingredient.phase_min,
            "product_type":     ingredient.product_type,
            "time":             ingredient.time,
        }

    cache.set("ingredient_db", result, timeout=3600)
    return result


def get_concern_timelines():
    """
    Returns CONCERN_TIMELINES format dict from database.
    {
        "acne": {"weeks": "4-6", "popup": "...", "purge_warning": True},
        ...
    }
    """
    cached = cache.get("concern_timelines")
    if cached is not None:
        return cached

    result = {}

    for timeline in ConcernTimeline.objects.filter(is_active=True):
        result[timeline.concern_key] = {
            "weeks":         timeline.weeks,
            "popup":         timeline.popup_text,
            "purge_warning": timeline.purge_warning,
        }

    cache.set("concern_timelines", result, timeout=3600)
    return result


def get_conflict_pairs():
    """
    Returns CONFLICT_PAIRS format list from database.
    [("acne", "dryness"), ("acne", "sensitivity"), ...]
    """
    cached = cache.get("conflict_pairs")
    if cached is not None:
        return cached

    result = []

    for pair in ConflictPair.objects.filter(is_active=True):
        result.append((pair.concern_a, pair.concern_b))

    cache.set("conflict_pairs", result, timeout=3600)
    return result


def get_avoid_map():
    """
    Returns AVOID_MAP format dict from database.
    {
        "acne": ["Coconut oil", "Heavy cream moisturizers", ...],
        "sensitivity": ["Alcohol denat", ...],
        ...
    }
    """
    cached = cache.get("avoid_map")
    if cached is not None:
        return cached

    result = {}

    for item in AvoidIngredient.objects.filter(is_active=True):
        if item.concern_key not in result:
            result[item.concern_key] = []
        result[item.concern_key].append(item.ingredient_name)

    cache.set("avoid_map", result, timeout=3600)
    return result


def get_plain_text_keywords():
    """
    Returns PLAIN_TEXT_KEYWORDS format dict from database.
    {
        "acne": ["pimple", "pimples", "breakout", ...],
        "pigmentation": ["dark spot", ...],
        ...
    }
    """
    cached = cache.get("plain_text_keywords")
    if cached is not None:
        return cached

    result = {}

    for item in PlainTextKeyword.objects.filter(is_active=True):
        if item.concern_key not in result:
            result[item.concern_key] = []
        result[item.concern_key].append(item.keyword)

    cache.set("plain_text_keywords", result, timeout=3600)
    return result


def get_next_goals():
    """
    Returns NEXT_GOALS format dict from database.
    {
        "acne": "Once breakouts are controlled...",
        ...
    }
    """
    cached = cache.get("next_goals")
    if cached is not None:
        return cached

    result = {}

    for item in NextGoal.objects.filter(is_active=True):
        result[item.concern_key] = item.goal_text

    cache.set("next_goals", result, timeout=3600)
    return result


def get_mask_db():
    """
    Returns MASK_DB format list from database.
    Includes nested ingredients and steps lists.
    Uses prefetch_related to load everything efficiently.

    [
        {
            "name": "Multani Mitti Cooling Mask",
            "benefit": "...",
            "frequency": "Once per week",
            "warning": "...",
            "for_types": ["Oily", "Combination"],
            "for_concerns": ["acne", "oiliness", ...],
            "avoid_if": ["Dry", "Sensitized", ...],
            "safe_level": "normal_only",
            "ingredients": ["2 tablespoons Multani Mitti", ...],
            "how_to_use": ["Mix all ingredients...", ...],
        },
        ...
    ]
    """
    cached = cache.get("mask_db")
    if cached is not None:
        return cached

    result = []

    masks = FaceMask.objects.filter(
        is_active=True
    ).prefetch_related("ingredients", "steps")

    for mask in masks:
        ingredient_list = []
        for ing in mask.ingredients.all():
            ingredient_list.append(ing.text)

        step_list = []
        for step in mask.steps.all():
            step_list.append(step.text)

        result.append({
            "name":         mask.name,
            "benefit":      mask.benefit,
            "frequency":    mask.frequency,
            "warning":      mask.warning,
            "for_types":    mask.get_for_types_list(),
            "for_concerns": mask.get_for_concerns_list(),
            "avoid_if":     mask.get_avoid_if_list(),
            "safe_level":   mask.safe_level,
            "ingredients":  ingredient_list,
            "how_to_use":   step_list,
        })

    cache.set("mask_db", result, timeout=3600)
    return result


def get_goals_db():
    """
    Returns GOALS_DB format dict from database.
    Includes nested phase3_ingredients list.

    {
        "glow": {
            "label": "Natural Glow",
            "key": "glow",
            "requires_stable": ["sensitivity", ...],
            "phase3_ingredients": ["Vitamin C 10%", ...],
            "roadmap_text": "...",
            "naturally_supported_by": ["dullness", ...],
        },
        ...
    }
    """
    cached = cache.get("goals_db")
    if cached is not None:
        return cached

    result = {}

    goals = SkinGoal.objects.filter(
        is_active=True
    ).prefetch_related("phase3_ingredients")

    for goal in goals:
        ingredient_list = []
        for ing in goal.phase3_ingredients.all():
            ingredient_list.append(ing.text)

        result[goal.key] = {
            "label":                  goal.label,
            "key":                    goal.key,
            "requires_stable":        goal.get_requires_stable_list(),
            "phase3_ingredients":     ingredient_list,
            "roadmap_text":           goal.roadmap_text,
            "naturally_supported_by": goal.get_naturally_supported_by_list(),
        }

    cache.set("goals_db", result, timeout=3600)
    return result


def get_product_db():
    """
    Returns product recommendations grouped by ingredient_key.

    {
        "niacinamide": [
            {
                "name": "The Ordinary Niacinamide 10% + Zinc 1%",
                "note": "Affordable and widely available in BD",
                "buy_link": "https://...",
                "compatible_skin_types": [],
                "sensitivity_safe": True,
                "budget_tier": "low",
            },
        ],
        ...
    }
    """
    cached = cache.get("product_db")
    if cached is not None:
        return cached

    result = {}

    for product in Product.objects.filter(is_active=True):
        key = product.ingredient_key
        if key not in result:
            result[key] = []
        result[key].append({
            "name":                  product.name,
            "note":                  product.note,
            "buy_link":              product.buy_link,
            "compatible_skin_types": product.get_compatible_types_list(),
            "sensitivity_safe":      product.sensitivity_safe,
            "budget_tier":           product.budget_tier,
        })

    cache.set("product_db", result, timeout=3600)
    return result


def clear_all_caches():
    """
    Clear every db_access cache key.
    Call this after bulk data loads to force fresh database reads.
    """
    keys = [
        "ingredient_db", "concern_timelines", "conflict_pairs",
        "avoid_map", "plain_text_keywords", "next_goals",
        "mask_db", "goals_db", "product_db",
    ]
    for key in keys:
        cache.delete(key)
