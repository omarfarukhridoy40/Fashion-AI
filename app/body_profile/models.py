from typing import Any, Dict, Optional, Tuple

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

User = settings.AUTH_USER_MODEL


class SkinType(models.TextChoices):
    NORMAL = "normal", "Normal"
    OILY = "oily", "Oily"
    DRY = "dry", "Dry"
    COMBINATION = "combination", "Combination"
    SENSITIVE = "sensitive", "Sensitive"


class Undertone(models.TextChoices):
    WARM = "warm", "Warm"
    COOL = "cool", "Cool"
    NEUTRAL = "neutral", "Neutral"


class VeinColor(models.TextChoices):
    GREEN = "green", "Green"
    BLUE_PURPLE = "blue", "Blue / Purple"
    MIXED = "mixed", "Mixed"


class FaceShape(models.TextChoices):
    OVAL = "oval", "Oval"
    ROUND = "round", "Round"
    SQUARE = "square", "Square"
    HEART = "heart", "Heart"
    DIAMOND = "diamond", "Diamond"


class BodyShape(models.TextChoices):
    TRIANGLE = "triangle", "Triangle"
    INVERTED_TRIANGLE = "inverted_triangle", "Inverted Triangle"
    RECTANGLE = "rectangle", "Rectangle"
    HOURGLASS = "hourglass", "Hourglass"
    OVAL = "oval", "Oval"


class Favourite_Season(models.TextChoices):
    SPRING = "spring", "Spring"
    SUMMER = "summer", "Summer"
    AUTUMN = "autumn", "Autumn"
    WINTER = "winter", "Winter"


VEIN_COLOR_TO_UNDERTONE: Dict[str, str] = {
    VeinColor.GREEN: Undertone.WARM,
    VeinColor.BLUE_PURPLE: Undertone.COOL,
    VeinColor.MIXED: Undertone.NEUTRAL,
}

# This below code need to be check and understand the purpose. Need to be refactored if necessary.
UNDERTONE_TO_SUGGESTED_SEASONS: Dict[str, Tuple[str, ...]] = {
    Undertone.WARM: (Favourite_Season.SPRING, Favourite_Season.AUTUMN),
    Undertone.COOL: (Favourite_Season.SUMMER, Favourite_Season.WINTER),
    Undertone.NEUTRAL: (Favourite_Season.SPRING, Favourite_Season.SUMMER, Favourite_Season.AUTUMN, Favourite_Season.WINTER),
}


PALETTES_BY_UNDERTONE: Dict[str, Dict[str, Any]] = {
    Undertone.WARM: {
        "metals": ["gold", "rose gold"],
        "neutrals": [
            {"name": "Ivory", "hex": "#FFFFF0"},
            {"name": "Camel", "hex": "#C19A6B"},
            {"name": "Warm Beige", "hex": "#E6D5B8"},
            {"name": "Chocolate", "hex": "#5A3E2B"},
        ],
        "colors": [
            {"name": "Coral", "hex": "#FF6F61"},
            {"name": "Peach", "hex": "#FFCBA4"},
            {"name": "Tomato Red", "hex": "#FF6347"},
            {"name": "Olive", "hex": "#808000"},
            {"name": "Mustard", "hex": "#D4A017"},
            {"name": "Turquoise", "hex": "#40E0D0"},
        ],
    },
    Undertone.COOL: {
        "metals": ["silver", "platinum"],
        "neutrals": [
            {"name": "Pure White", "hex": "#FFFFFF"},
            {"name": "Cool Gray", "hex": "#8F8F8F"},
            {"name": "Charcoal", "hex": "#36454F"},
            {"name": "Navy", "hex": "#000080"},
        ],
        "colors": [
            {"name": "Cobalt", "hex": "#0047AB"},
            {"name": "Emerald", "hex": "#50C878"},
            {"name": "Fuchsia", "hex": "#FF00FF"},
            {"name": "Berry", "hex": "#8A2BE2"},
            {"name": "Icy Pink", "hex": "#F8C8DC"},
            {"name": "Teal", "hex": "#008080"},
        ],
    },
    Undertone.NEUTRAL: {
        "metals": ["gold", "silver"],
        "neutrals": [
            {"name": "Soft White", "hex": "#F8F5F0"},
            {"name": "Taupe", "hex": "#B38B6D"},
            {"name": "Stone", "hex": "#A8A29E"},
            {"name": "Espresso", "hex": "#3B2F2F"},
        ],
        "colors": [
            {"name": "Dusty Rose", "hex": "#DCAE96"},
            {"name": "Jade", "hex": "#00A86B"},
            {"name": "Plum", "hex": "#8E4585"},
            {"name": "Sage", "hex": "#9CAF88"},
            {"name": "Denim", "hex": "#1560BD"},
            {"name": "Burgundy", "hex": "#800020"},
        ],
    },
}


class BodyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="body_profile")

    # Basic
    height_cm = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])
    weight_kg = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])

    # Measurements
    chest_cm = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])
    waist_cm = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])
    hips_cm = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])
    shoulder_cm = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])

    # Shape
    body_shape = models.CharField(max_length=20, choices=BodyShape.choices, blank=True)
    face_shape = models.CharField(max_length=20, choices=FaceShape.choices, blank=True)

    # Skin analysis
    skin_type = models.CharField(max_length=20, choices=SkinType.choices, blank=True)
    vein_color = models.CharField(max_length=10, choices=VeinColor.choices, blank=True)
    undertone = models.CharField(
        max_length=10,
        choices=Undertone.choices,
        blank=True,
        editable=False,
        help_text="Auto-derived from vein_color (green=warm, blue/purple=cool, mixed=neutral).",
    )
    favourite_season = models.CharField(max_length=10, choices=Favourite_Season.choices, blank=True)

    # Recommended colors
    recommended_palette = models.JSONField(null=True, blank=True)

    # Clothing sizes
    shirt_size = models.CharField(max_length=10, blank=True)
    pants_size = models.CharField(max_length=10, blank=True)
    shoe_size = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])

    # Photos for AI later
    body_photo = models.ImageField(upload_to="body_photos/", null=True, blank=True)
    face_photo = models.ImageField(upload_to="face_photos/", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def inferred_undertone(self) -> str:
        if not self.vein_color:
            return ""
        return VEIN_COLOR_TO_UNDERTONE.get(self.vein_color, "")

    @property
    def suggested_seasons(self) -> Tuple[str, ...]:
        undertone = self.inferred_undertone or self.undertone
        if not undertone:
            return tuple()
        return UNDERTONE_TO_SUGGESTED_SEASONS.get(undertone, tuple())

    def build_recommended_palette(self) -> Optional[Dict[str, Any]]:
        undertone = self.inferred_undertone or self.undertone
        if not undertone:
            return None

        palette = PALETTES_BY_UNDERTONE.get(undertone)
        if not palette:
            return None

        return {
            "undertone": undertone,
            "vein_color": self.vein_color or None,
            "season": self.favourite_season or None,
            **palette,
        }

    def save(self, *args, **kwargs):
        self.undertone = self.inferred_undertone
        self.recommended_palette = self.build_recommended_palette()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} Body Profile"
