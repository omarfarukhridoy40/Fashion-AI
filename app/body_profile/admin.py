from django.contrib import admin

from .models import BodyProfile


@admin.register(BodyProfile)
class BodyProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "skin_type",
        "vein_color",
        "undertone",
        "favourite_season",
        "body_shape",
        "face_shape",
        "created_at",
    )
    list_select_related = ("user",)
    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
    )
    list_filter = (
        "skin_type",
        "vein_color",
        "undertone",
        "favourite_season",
        "body_shape",
        "face_shape",
        "created_at",
    )
    readonly_fields = ("undertone", "recommended_palette", "created_at")
