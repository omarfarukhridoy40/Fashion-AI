from django.contrib import admin
from django.core.cache import cache

from .models import (
    Ingredient, ConcernTimeline, ConflictPair, AvoidIngredient,
    PlainTextKeyword, NextGoal,
    FaceMask, FaceMaskIngredient, FaceMaskStep,
    SkinGoal, SkinGoalIngredient,
    Product, UserSkinProfile,
)


# =============================================================================
# INLINE CLASSES
# These show related records as rows inside the parent record's edit page.
# =============================================================================

class FaceMaskIngredientInline(admin.TabularInline):
    model = FaceMaskIngredient
    extra = 1
    ordering = ["order"]
    fields = ["order", "text"]


class FaceMaskStepInline(admin.TabularInline):
    model = FaceMaskStep
    extra = 1
    ordering = ["order"]
    fields = ["order", "text"]


class SkinGoalIngredientInline(admin.TabularInline):
    model = SkinGoalIngredient
    extra = 1
    ordering = ["order"]
    fields = ["order", "text"]


# =============================================================================
# INGREDIENT
# =============================================================================

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ["label", "key", "phase_min", "sensitivity_safe", "dehydrated_safe", "time", "is_active"]
    list_filter = ["sensitivity_safe", "dehydrated_safe", "phase_min", "is_active"]
    search_fields = ["key", "label", "targets"]
    list_editable = ["is_active"]
    fieldsets = [
        ("Identity",           {"fields": ["key", "label", "is_active"]}),
        ("Clinical Info",      {"fields": ["why", "targets", "product_type", "time"]}),
        ("Safety and Phase",   {"fields": ["sensitivity_safe", "dehydrated_safe", "phase_min"]}),
    ]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        cache.delete("ingredient_db")


# =============================================================================
# CONCERN TIMELINE
# =============================================================================

@admin.register(ConcernTimeline)
class ConcernTimelineAdmin(admin.ModelAdmin):
    list_display = ["concern_key", "weeks", "purge_warning", "is_active"]
    list_filter = ["purge_warning", "is_active"]
    list_editable = ["is_active"]
    search_fields = ["concern_key", "popup_text"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        cache.delete("concern_timelines")


# =============================================================================
# CONFLICT PAIR
# =============================================================================

@admin.register(ConflictPair)
class ConflictPairAdmin(admin.ModelAdmin):
    list_display = ["concern_a", "concern_b", "is_active"]
    list_editable = ["is_active"]
    search_fields = ["concern_a", "concern_b"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        cache.delete("conflict_pairs")


# =============================================================================
# AVOID INGREDIENT
# =============================================================================

@admin.register(AvoidIngredient)
class AvoidIngredientAdmin(admin.ModelAdmin):
    list_display = ["concern_key", "ingredient_name", "is_active"]
    list_filter = ["concern_key", "is_active"]
    list_editable = ["is_active"]
    search_fields = ["concern_key", "ingredient_name"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        cache.delete("avoid_map")


# =============================================================================
# PLAIN TEXT KEYWORD
# =============================================================================

@admin.register(PlainTextKeyword)
class PlainTextKeywordAdmin(admin.ModelAdmin):
    list_display = ["keyword", "concern_key", "is_active"]
    list_filter = ["concern_key", "is_active"]
    list_editable = ["is_active"]
    search_fields = ["keyword", "concern_key"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        cache.delete("plain_text_keywords")


# =============================================================================
# NEXT GOAL
# =============================================================================

@admin.register(NextGoal)
class NextGoalAdmin(admin.ModelAdmin):
    list_display = ["concern_key", "is_active"]
    list_editable = ["is_active"]
    search_fields = ["concern_key", "goal_text"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        cache.delete("next_goals")


# =============================================================================
# FACE MASK
# =============================================================================

@admin.register(FaceMask)
class FaceMaskAdmin(admin.ModelAdmin):
    list_display = ["name", "safe_level", "frequency", "is_active"]
    list_filter = ["safe_level", "is_active"]
    list_editable = ["is_active"]
    search_fields = ["name", "benefit"]
    inlines = [FaceMaskIngredientInline, FaceMaskStepInline]
    fieldsets = [
        ("Identity",  {"fields": ["name", "benefit", "frequency", "warning", "is_active"]}),
        ("Targeting", {"fields": ["for_types", "for_concerns", "avoid_if", "safe_level"],
                       "description": "Controls which users receive this mask."}),
    ]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        cache.delete("mask_db")


# =============================================================================
# SKIN GOAL
# =============================================================================

@admin.register(SkinGoal)
class SkinGoalAdmin(admin.ModelAdmin):
    list_display = ["label", "key", "is_active"]
    list_editable = ["is_active"]
    search_fields = ["key", "label", "roadmap_text"]
    inlines = [SkinGoalIngredientInline]
    fieldsets = [
        ("Identity", {"fields": ["key", "label", "is_active"]}),
        ("Content",  {"fields": ["roadmap_text"]}),
        ("Logic",    {"fields": ["requires_stable", "naturally_supported_by"],
                      "description": "requires_stable: comma-separated concerns that block this goal. naturally_supported_by: concerns whose treatment also moves toward this goal."}),
    ]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        cache.delete("goals_db")


# =============================================================================
# PRODUCT
# =============================================================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "ingredient_key", "budget_tier", "sensitivity_safe", "is_active"]
    list_filter = ["budget_tier", "sensitivity_safe", "is_active"]
    list_editable = ["is_active"]
    search_fields = ["name", "ingredient_key", "note"]
    fieldsets = [
        ("Product",  {"fields": ["ingredient_key", "name", "note", "buy_link", "is_active"]}),
        ("Matching", {"fields": ["compatible_skin_types", "sensitivity_safe", "budget_tier"],
                      "description": "Controls which users receive this product card."}),
    ]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        cache.delete("product_db")


# =============================================================================
# USER SKIN PROFILE
# =============================================================================

@admin.register(UserSkinProfile)
class UserSkinProfileAdmin(admin.ModelAdmin):
    list_display = ["__str__", "skin_type", "conflict_detected", "primary_concern", "created_at"]
    list_filter = ["skin_type", "conflict_detected"]
    search_fields = ["skin_type", "primary_concern", "session_key"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = [
        ("Profile",           {"fields": ["linked_user", "session_key", "skin_type", "skin_states", "top_concerns"]}),
        ("Analysis Result",   {"fields": ["conflict_detected", "primary_concern", "routine_start_date"]}),
        ("Timestamps",        {"fields": ["created_at", "updated_at"]}),
    ]
