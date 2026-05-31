from django.core.management.base import BaseCommand
from django.db import transaction

from skin.models import Ingredient, Product


# Every demo row's name begins with this literal prefix. The command identifies
# its OWN rows solely by this prefix — it never reads, modifies, or deletes a
# Product whose name lacks it (those are real/curated rows).
DEMO_PREFIX = "[DEMO] "


class Command(BaseCommand):
    help = "Seed deterministic DEMO Product rows (3 per active Ingredient) for testing product recommendations."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help='Delete ONLY demo products (name starts with "[DEMO] ") and exit without reseeding.',
        )

    def handle(self, *args, **options):
        # --clear: remove only our own prefixed rows, report the count, and stop.
        # This never touches a non-demo Product because the filter is scoped to
        # the "[DEMO] " name prefix.
        if options["clear"]:
            deleted, _ = Product.objects.filter(name__startswith=DEMO_PREFIX).delete()
            self.stdout.write(
                self.style.SUCCESS(f"Removed {deleted} demo product row(s). Nothing reseeded.")
            )
            return

        self.stdout.write("Seeding demo products...")

        # Read-only on Ingredient. Seed products only for keys that actually
        # exist — a product whose ingredient_key has no Ingredient can never
        # match anything in a routine. Ordered by key (model default) for
        # deterministic output.
        ingredients = list(Ingredient.objects.filter(is_active=True))

        # Empty-ingredients guard: do not crash, tell the user what to run first.
        if not ingredients:
            self.stdout.write(
                self.style.WARNING(
                    "No active Ingredient rows found. Run the ingredient seed command first "
                    "(e.g. `python manage.py initial_db_load`), then re-run this command."
                )
            )
            return

        created = updated = 0

        # transaction.atomic so a mid-run failure cannot leave a half-seeded state
        # — either every demo row for this run lands, or none does.
        with transaction.atomic():
            for ingredient in ingredients:
                for spec in self._demo_specs(ingredient):
                    # update_or_create keyed on (ingredient_key, name) makes the
                    # command idempotent: re-running REFRESHES the same rows
                    # instead of duplicating them. The name (with its budget tier
                    # suffix) is stable per ingredient, so the key is stable.
                    _, was_created = Product.objects.update_or_create(
                        ingredient_key=spec["ingredient_key"],
                        name=spec["name"],
                        defaults=spec["defaults"],
                    )
                    created, updated = self._count(created, updated, was_created)

        total = created + updated
        self.stdout.write(
            f"  Demo products: {created} created, {updated} updated "
            f"({total} total across {len(ingredients)} ingredient(s))"
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Done. All rows are demo data (name starts with "{DEMO_PREFIX}") '
                "and can be removed with `--clear`."
            )
        )

    @staticmethod
    def _demo_specs(ingredient):
        """
        Build the deterministic 3-product spread for one Ingredient.

        The spread deliberately exercises every filter branch:
          1. Budget Pick     — low,    sensitivity_safe=True,  all types
          2. Mid-Range       — medium, sensitivity_safe=False, all types
          3. Premium         — high,   sensitivity_safe=True,  Oily only
        """
        key = ingredient.key
        label = ingredient.label

        return [
            {
                "ingredient_key": key,
                "name": f"{DEMO_PREFIX}{label} — Budget Pick",
                "defaults": {
                    "note": "Affordable demo pick — widely available.",
                    "buy_link": f"https://example.com/demo/{key}-budget",
                    "compatible_skin_types": "",   # blank = all skin types
                    "sensitivity_safe": True,
                    "budget_tier": "low",
                    "is_active": True,
                },
            },
            {
                "ingredient_key": key,
                "name": f"{DEMO_PREFIX}{label} — Mid-Range",
                "defaults": {
                    "note": "Mid-range demo pick.",
                    "buy_link": f"https://example.com/demo/{key}-mid",
                    "compatible_skin_types": "",   # blank = all skin types
                    "sensitivity_safe": False,
                    "budget_tier": "medium",
                    "is_active": True,
                },
            },
            {
                "ingredient_key": key,
                "name": f"{DEMO_PREFIX}{label} — Premium (Oily only)",
                "defaults": {
                    "note": "Premium demo pick, oily-skin targeted.",
                    "buy_link": f"https://example.com/demo/{key}-premium",
                    # "Oily" is a real engine skin type (logic.py calculate_skin_type).
                    "compatible_skin_types": "Oily",
                    "sensitivity_safe": True,
                    "budget_tier": "high",
                    "is_active": True,
                },
            },
        ]

    @staticmethod
    def _count(created, updated, was_created):
        # Mirror of the existing seed command's counter, adapted for
        # update_or_create (created vs. refreshed-existing).
        if was_created:
            return created + 1, updated
        return created, updated + 1
