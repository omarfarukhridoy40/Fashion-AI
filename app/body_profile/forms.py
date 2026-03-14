from django import forms
from .models import BodyProfile


class BodyProfileForm(forms.ModelForm):

    class Meta:
        model = BodyProfile
        fields = [
            # Ask these first (your flow)
            "skin_type",
            "vein_color",
            "favourite_season",

            # Basic
            "height_cm",
            "weight_kg",

            # Measurements
            "chest_cm",
            "waist_cm",
            "hips_cm",
            "shoulder_cm",

            # Shape
            "body_shape",
            "face_shape",

            # Clothing sizes
            "shirt_size",
            "pants_size",
            "shoe_size",

            # Photos for AI later
            "body_photo",
            "face_photo",
        ]

        widgets = {
            "height_cm": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": 0.01}),
            "weight_kg": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": 0.01}),

            "chest_cm": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": 0.01}),
            "waist_cm": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": 0.01}),
            "hips_cm": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": 0.01}),
            "shoulder_cm": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": 0.01}),

            "body_shape": forms.Select(attrs={"class": "form-select"}),
            "face_shape": forms.Select(attrs={"class": "form-select"}),

            "skin_type": forms.Select(attrs={"class": "form-select"}),
            "vein_color": forms.Select(attrs={"class": "form-select"}),

            "favourite_season": forms.Select(attrs={"class": "form-select"}),

            "shirt_size": forms.TextInput(attrs={"class": "form-control"}),
            "pants_size": forms.TextInput(attrs={"class": "form-control"}),
            "shoe_size": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": 0.5}),

            "body_photo": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "face_photo": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
        }

    def save(self, commit=True):
        """
        Keep model-owned fields model-owned.
        These are auto-derived in BodyProfile.save():
        - undertone
        - recommended_palette
        """
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()
        return instance
