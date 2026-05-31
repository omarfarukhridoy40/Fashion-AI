from django.conf import settings
from django.db import models


# =============================================================================
# TABLE 1 — Ingredient
# Replaces INGREDIENT_DB in logic.py
# =============================================================================

class Ingredient(models.Model):

    # Internal key used in code — e.g. "niacinamide"
    # unique=True means no two ingredients can share the same key
    key = models.CharField(
        max_length=100,
        unique=True,
        help_text="Internal code key — e.g. niacinamide, salicylic_acid. Must match logic.py.",
    )

    # Display name shown to the user — e.g. "Niacinamide 5%"
    label = models.CharField(
        max_length=200,
        help_text="Display name shown in the routine — e.g. Niacinamide 5%",
    )

    # One sentence shown in the ingredient intelligence section
    why = models.TextField(
        help_text="Why this ingredient is used — shown to the user on the result page",
    )

    # Which concerns this helps — stored as comma-separated string
    # Helper method get_targets_list() converts back to Python list
    targets = models.TextField(
        help_text="Comma-separated concern keys — e.g. acne,oiliness,dullness",
    )

    # Safety flags
    sensitivity_safe = models.BooleanField(
        default=False,
        help_text="True = safe for reaction=burning or redness users",
    )
    dehydrated_safe = models.BooleanField(
        default=False,
        help_text="True = safe for Dehydrated skin state users",
    )

    # Earliest phase this ingredient can be introduced
    # 1 = Phase 1 (foundation only), 2 = Phase 2 (treatment), 3 = Phase 3 (enhancement)
    phase_min = models.IntegerField(
        default=2,
        help_text="Earliest phase: 1=foundation, 2=treatment, 3=enhancement",
    )

    # What kind of product this ingredient appears in
    product_type = models.CharField(
        max_length=100,
        help_text="e.g. serum, moisturizer, toner/cleanser, eye cream",
    )

    # When to apply
    time = models.CharField(
        max_length=20,
        help_text="AM, PM, or AM/PM",
    )

    # Soft delete — set False to disable without removing from database
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to disable without deleting",
    )

    # Django fills these automatically
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.label} ({self.key})"

    def get_targets_list(self):
        """
        Return targets as a Python list.
        "acne,oiliness,dullness" becomes ["acne", "oiliness", "dullness"]
        """
        result = []
        for item in self.targets.split(","):
            cleaned = item.strip()
            if cleaned:
                result.append(cleaned)
        return result

    class Meta:
        ordering = ["key"]
        verbose_name = "Ingredient"
        verbose_name_plural = "Ingredients"


# =============================================================================
# TABLE 2 — ConcernTimeline
# Replaces CONCERN_TIMELINES in logic.py
# =============================================================================

class ConcernTimeline(models.Model):

    concern_key = models.CharField(
        max_length=100,
        unique=True,
        help_text="Concern key — e.g. acne, pigmentation, dullness",
    )

    # Shown as text — e.g. "4-6"
    weeks = models.CharField(
        max_length=20,
        help_text="Expected improvement window — e.g. 4-6 or 8-12",
    )

    # Full message shown in the timeline popup on the result page
    popup_text = models.TextField(
        help_text="Message shown in the timeline popup card on the result page",
    )

    # True for acne (purging) and aging (retinoid adjustment period)
    purge_warning = models.BooleanField(
        default=False,
        help_text="True if skin may temporarily worsen before improving",
    )

    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.concern_key} — {self.weeks} weeks"

    class Meta:
        ordering = ["concern_key"]
        verbose_name = "Concern Timeline"
        verbose_name_plural = "Concern Timelines"


# =============================================================================
# TABLE 3 — ConflictPair
# Replaces CONFLICT_PAIRS in logic.py
# =============================================================================

class ConflictPair(models.Model):

    concern_a = models.CharField(
        max_length=100,
        help_text="First concern in the conflict pair",
    )
    concern_b = models.CharField(
        max_length=100,
        help_text="Second concern in the conflict pair",
    )

    # Admin reference — explains why they conflict
    reason = models.TextField(
        blank=True,
        help_text="Why these concerns conflict — for admin documentation only",
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to disable this conflict pair without deleting",
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.concern_a}  +  {self.concern_b}"

    class Meta:
        unique_together = [["concern_a", "concern_b"]]
        ordering = ["concern_a", "concern_b"]
        verbose_name = "Conflict Pair"
        verbose_name_plural = "Conflict Pairs"


# =============================================================================
# TABLE 4 — AvoidIngredient
# Replaces AVOID_MAP in logic.py
# One row per ingredient-to-avoid per concern
# =============================================================================

class AvoidIngredient(models.Model):

    concern_key = models.CharField(
        max_length=100,
        help_text="Concern that triggers this avoidance — e.g. acne",
    )
    ingredient_name = models.CharField(
        max_length=200,
        help_text="Ingredient to avoid — shown as red tag on result page",
    )

    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Avoid {self.ingredient_name}  (for {self.concern_key})"

    class Meta:
        unique_together = [["concern_key", "ingredient_name"]]
        ordering = ["concern_key", "ingredient_name"]
        verbose_name = "Avoid Ingredient"
        verbose_name_plural = "Avoid Ingredients"


# =============================================================================
# TABLE 5 — PlainTextKeyword
# Replaces PLAIN_TEXT_KEYWORDS in logic.py
# One row per keyword per concern
# =============================================================================

class PlainTextKeyword(models.Model):

    concern_key = models.CharField(
        max_length=100,
        help_text="Concern this keyword maps to — e.g. acne",
    )
    keyword = models.CharField(
        max_length=100,
        help_text="Keyword to scan for in user description — store lowercase — e.g. pimple",
    )

    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'"{self.keyword}"  →  {self.concern_key}'

    class Meta:
        unique_together = [["concern_key", "keyword"]]
        ordering = ["concern_key", "keyword"]
        verbose_name = "Plain Text Keyword"
        verbose_name_plural = "Plain Text Keywords"


# =============================================================================
# TABLE 6 — NextGoal
# Replaces NEXT_GOALS in logic.py
# =============================================================================

class NextGoal(models.Model):

    concern_key = models.CharField(
        max_length=100,
        unique=True,
        help_text="Concern key this next goal applies to",
    )
    goal_text = models.TextField(
        help_text="Text shown at the bottom of the result page after the timeline",
    )

    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Next goal after: {self.concern_key}"

    class Meta:
        ordering = ["concern_key"]
        verbose_name = "Next Goal"
        verbose_name_plural = "Next Goals"


# =============================================================================
# TABLE 7 — FaceMask
# Main mask record — replaces MASK_DB in masks.py
# Ingredient lines and steps are in separate tables linked by ForeignKey
# =============================================================================

class FaceMask(models.Model):

    name = models.CharField(
        max_length=200,
        help_text="Mask name — e.g. Multani Mitti Cooling Mask",
    )
    benefit = models.TextField(
        help_text="One sentence about what this mask does",
    )
    frequency = models.CharField(
        max_length=100,
        help_text="How often to use — e.g. Once per week",
    )
    warning = models.TextField(
        blank=True,
        help_text="Safety warning shown at bottom of card — leave blank if none",
    )

    # Comma-separated skin types this mask suits
    for_types = models.TextField(
        help_text="Comma-separated skin types — e.g. Oily,Combination",
    )

    # Comma-separated concern keys this mask helps
    for_concerns = models.TextField(
        help_text="Comma-separated concern keys — e.g. acne,oiliness,comedones",
    )

    # Comma-separated disqualifiers — skin types, states, or concern names
    avoid_if = models.TextField(
        blank=True,
        help_text="Comma-separated disqualifiers — e.g. Dry,Sensitized,Compromised Barrier",
    )

    SAFE_LEVEL_CHOICES = [
        ("all",         "All skin including sensitive"),
        ("normal_only", "Normal skin only — not for sensitized or compromised barrier"),
    ]
    safe_level = models.CharField(
        max_length=20,
        choices=SAFE_LEVEL_CHOICES,
        default="normal_only",
        help_text="Who can receive this mask recommendation",
    )

    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_for_types_list(self):
        result = []
        for item in self.for_types.split(","):
            cleaned = item.strip()
            if cleaned:
                result.append(cleaned)
        return result

    def get_for_concerns_list(self):
        result = []
        for item in self.for_concerns.split(","):
            cleaned = item.strip()
            if cleaned:
                result.append(cleaned)
        return result

    def get_avoid_if_list(self):
        result = []
        if not self.avoid_if:
            return result
        for item in self.avoid_if.split(","):
            cleaned = item.strip()
            if cleaned:
                result.append(cleaned)
        return result

    class Meta:
        ordering = ["name"]
        verbose_name = "Face Mask"
        verbose_name_plural = "Face Masks"


# =============================================================================
# TABLE 8 — FaceMaskIngredient
# One row per ingredient line in a mask recipe
# Linked to FaceMask via ForeignKey
# =============================================================================

class FaceMaskIngredient(models.Model):

    # ForeignKey creates the link — many ingredients can belong to one mask
    # on_delete=CASCADE: if the mask is deleted, its ingredients are deleted too
    # related_name="ingredients" lets us write mask.ingredients.all()
    mask = models.ForeignKey(
        FaceMask,
        on_delete=models.CASCADE,
        related_name="ingredients",
        help_text="The mask this ingredient belongs to",
    )
    text = models.CharField(
        max_length=300,
        help_text="Full ingredient line — e.g. 2 tablespoons Multani Mitti",
    )
    order = models.IntegerField(
        default=0,
        help_text="Display order — lower number shows first",
    )

    def __str__(self):
        return f"{self.mask.name}: {self.text}"

    class Meta:
        ordering = ["order"]
        verbose_name = "Mask Ingredient"
        verbose_name_plural = "Mask Ingredients"


# =============================================================================
# TABLE 9 — FaceMaskStep
# One row per how-to-use step per mask
# Linked to FaceMask via ForeignKey
# =============================================================================

class FaceMaskStep(models.Model):

    mask = models.ForeignKey(
        FaceMask,
        on_delete=models.CASCADE,
        related_name="steps",
        help_text="The mask this step belongs to",
    )
    text = models.CharField(
        max_length=500,
        help_text="Full instruction for this step",
    )
    order = models.IntegerField(
        default=0,
        help_text="Display order — lower number shows first",
    )

    def __str__(self):
        return f"{self.mask.name}  step {self.order}"

    class Meta:
        ordering = ["order"]
        verbose_name = "Mask Step"
        verbose_name_plural = "Mask Steps"


# =============================================================================
# TABLE 10 — SkinGoal
# Main goal record — replaces GOALS_DB in goals.py
# Phase 3 ingredients are in SkinGoalIngredient linked by ForeignKey
# =============================================================================

class SkinGoal(models.Model):

    key = models.CharField(
        max_length=100,
        unique=True,
        help_text="Internal key — e.g. glow, glass_skin, pore_minimizing",
    )
    label = models.CharField(
        max_length=200,
        help_text="Checkbox label shown on the form — e.g. Natural Glow",
    )
    roadmap_text = models.TextField(
        help_text="Explanation shown in Phase 3 goal card on the result page",
    )

    # Concerns that must be resolved before this goal activates
    # Empty = no prerequisites (goal is always active)
    requires_stable = models.TextField(
        blank=True,
        help_text="Comma-separated concern keys that block this goal — leave blank if no prerequisites",
    )

    # Concerns whose treatment also moves toward this goal
    naturally_supported_by = models.TextField(
        blank=True,
        help_text="Comma-separated concern keys whose treatment also supports this goal",
    )

    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.label}  ({self.key})"

    def get_requires_stable_list(self):
        result = []
        if not self.requires_stable:
            return result
        for item in self.requires_stable.split(","):
            cleaned = item.strip()
            if cleaned:
                result.append(cleaned)
        return result

    def get_naturally_supported_by_list(self):
        result = []
        if not self.naturally_supported_by:
            return result
        for item in self.naturally_supported_by.split(","):
            cleaned = item.strip()
            if cleaned:
                result.append(cleaned)
        return result

    class Meta:
        ordering = ["label"]
        verbose_name = "Skin Goal"
        verbose_name_plural = "Skin Goals"


# =============================================================================
# TABLE 11 — SkinGoalIngredient
# One row per Phase 3 ingredient per goal
# Linked to SkinGoal via ForeignKey
# =============================================================================

class SkinGoalIngredient(models.Model):

    goal = models.ForeignKey(
        SkinGoal,
        on_delete=models.CASCADE,
        related_name="phase3_ingredients",
        help_text="The goal this Phase 3 ingredient belongs to",
    )
    text = models.CharField(
        max_length=300,
        help_text="Phase 3 ingredient shown in the goal card — e.g. Vitamin C 10%",
    )
    order = models.IntegerField(
        default=0,
        help_text="Display order — lower number shows first",
    )

    def __str__(self):
        return f"{self.goal.label}: {self.text}"

    class Meta:
        ordering = ["order"]
        verbose_name = "Goal Ingredient"
        verbose_name_plural = "Goal Ingredients"


# =============================================================================
# TABLE 12 — Product
# Manually curated product recommendations (Phase 2 — starts empty)
#
# Admin adds products one by one.
# The engine only shows a product card if a match exists.
# If no match exists, the routine step shows ingredient only — no fabrication.
# =============================================================================

class Product(models.Model):

    # Must match a key in Ingredient table
    ingredient_key = models.CharField(
        max_length=100,
        help_text="Ingredient key this product is recommended for — must match Ingredient.key",
    )

    name = models.CharField(
        max_length=300,
        help_text="Full product name as shown on the result page",
    )

    # Short note about why this specific product
    note = models.CharField(
        max_length=300,
        help_text="Short reason this product was chosen — e.g. Affordable and widely available in BD",
    )

    # Optional affiliate or purchase link
    buy_link = models.URLField(
        blank=True,
        help_text="Purchase or affiliate link — leave blank if not available",
    )

    # Comma-separated compatible skin types — empty means all types
    compatible_skin_types = models.TextField(
        blank=True,
        help_text="Comma-separated skin types — leave blank for all types",
    )

    sensitivity_safe = models.BooleanField(
        default=False,
        help_text="True = safe to recommend to reactive skin users",
    )

    BUDGET_CHOICES = [
        ("low",    "Low — under 500 BDT"),
        ("medium", "Medium — 500 to 1500 BDT"),
        ("high",   "High — over 1500 BDT"),
    ]
    budget_tier = models.CharField(
        max_length=20,
        choices=BUDGET_CHOICES,
        default="medium",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}  ({self.ingredient_key})"

    def get_compatible_types_list(self):
        """Return compatible_skin_types as a list. Empty list = all types allowed."""
        if not self.compatible_skin_types.strip():
            return []
        result = []
        for item in self.compatible_skin_types.split(","):
            cleaned = item.strip()
            if cleaned:
                result.append(cleaned)
        return result

    class Meta:
        ordering = ["ingredient_key", "name"]
        verbose_name = "Product"
        verbose_name_plural = "Products"


# =============================================================================
# TABLE 13 — UserSkinProfile
# Saves a user's analysis result (Phase 2 stub — partial implementation)
#
# In Phase 1: session_key tracks anonymous users
# In Phase 2: linked_user links to Django auth.User
# =============================================================================

class UserSkinProfile(models.Model):

    # Optional user account link — null until Phase 2 user accounts exist
    linked_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="skin_profiles",
        help_text="Linked user account — null until user accounts are implemented",
    )

    # Anonymous session tracking before user accounts
    session_key = models.CharField(
        max_length=100,
        blank=True,
        help_text="Django session key for anonymous tracking",
    )

    skin_type = models.CharField(max_length=50)
    skin_states = models.TextField(blank=True, help_text="Comma-separated detected state names")
    top_concerns = models.TextField(blank=True, help_text="Comma-separated top concern keys")

    # Raw questionnaire submission, stored losslessly as a dict-of-lists
    # ({field: [values]}). This is the verbatim user input (NOT computed output),
    # so a later "View full routine" brief can rebuild a QueryDict from it and
    # re-run the engine to regenerate the full routine on demand.
    # default=dict (a callable, not a shared mutable) so rows created before this
    # field migrate cleanly to an empty {} with no data migration; blank=True for
    # admin/forms. On PostgreSQL this maps to native JSONB.
    raw_input = models.JSONField(default=dict, blank=True)

    conflict_detected = models.BooleanField(default=False)
    primary_concern = models.CharField(max_length=100, blank=True)

    # Set when the user taps the Start Routine button
    routine_start_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When user started their routine — set when Start button is tapped",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.linked_user:
            return f"{self.linked_user.username} — {self.skin_type} — {self.created_at.date()}"
        return f"Anonymous — {self.skin_type} — {self.created_at.date()}"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "User Skin Profile"
        verbose_name_plural = "User Skin Profiles"
