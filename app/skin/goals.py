# ═══════════════════════════════════════════════════════════════════════════════
# goals.py — Skin Goals Database and Roadmap Generator
#
# Goals are what the user WANTS their skin to look like.
# Concerns are what is WRONG with their skin right now.
#
# Goals never override concerns. Goals sit in Phase 3 of the plan.
# This file figures out which goals are achievable, what is blocking them,
# and how the routine already supports them over time.
# ═══════════════════════════════════════════════════════════════════════════════


# ───────────────────────────────────────────────────────────────────────────────
# GOALS DATABASE
#
# Each goal has:
#   label            - what the user sees on the form (checkbox text)
#   key              - internal identifier
#   requires_stable  - list of concerns that must be resolved first
#                      if ANY of these are in top_concerns, the goal is blocked
#   phase3_ingredients - ingredients that support this goal in Phase 3
#   roadmap_text     - explanation shown to user about this goal
#   naturally_supported_by - concerns whose treatment also moves toward this goal
#                            even in Phase 1 or 2
# ───────────────────────────────────────────────────────────────────────────────


# =============================================================================
# GOALS DATABASE — now loaded from PostgreSQL via db_access.py
#
# All goal records including Phase 3 ingredients are stored in the database.
# Admin panel: /admin/skin_profile/skingoal/
#
# The functions below load from database each call.
# Data is cached by db_access.py for 1 hour.
import logging

from .db_access import get_goals_db


logger = logging.getLogger(__name__)


def build_goal_roadmap(selected_goals, top_concerns, conflict_detected):

    # Load goals from database (cached — fast after first load)
    GOALS_DB = get_goals_db()

    # If no goals selected, return empty list
    # The result page simply does not show the goals section
    if not selected_goals:
        return []

    roadmap = []

    for goal_key in selected_goals:

        # Skip if this goal is not in our database.
        # Log a warning so we have visibility in production if someone
        # submits an invalid goal key via a crafted POST request, or if
        # a new form option was added without updating goals.py / the DB.
        if goal_key not in GOALS_DB:
            logger.warning(f"Unknown skin_goal key received and skipped: {goal_key!r}")
            continue

        goal = GOALS_DB[goal_key]

        # Check if any blocking concerns are in the user's top concerns
        blocking_concerns = []
        for required_stable in goal["requires_stable"]:
            if required_stable in top_concerns:
                blocking_concerns.append(required_stable)

        # Also mark as blocked if there is a conflict — because conflict means
        # the user is still in Phase 1 barrier repair and nothing else can start yet
        if conflict_detected and goal["requires_stable"]:
            is_blocked = True
        else:
            is_blocked = len(blocking_concerns) > 0

        # Build the blocking reason text
        if is_blocked:
            if conflict_detected:
                blocking_reason = (
                    "Your skin currently has conflicting concerns that require a phased repair approach. "
                    "This goal will become the focus of Phase 3 once your skin is stable."
                )
            else:
                # Make a readable list of the blocking concerns
                concern_labels = {
                    "acne": "active acne",
                    "sensitivity": "skin reactivity",
                    "barrier_damage_acne": "barrier-damage acne",
                    "comedones": "active pore congestion",
                    "oiliness": "uncontrolled oiliness",
                    "dryness": "skin dryness",
                    "pigmentation": "active pigmentation",
                }
                readable_blocks = []
                for concern in blocking_concerns:
                    readable_blocks.append(concern_labels.get(concern, concern))

                blocking_reason = (
                    "This goal is delayed because your skin currently has: "
                    + ", ".join(readable_blocks)
                    + ". "
                    "These concerns are being addressed in Phase 2. "
                    "Once stable, Phase 3 will work toward this goal."
                )
        else:
            blocking_reason = None

        # Check which Phase 2 ingredients already support this goal
        already_helping = []
        for concern in goal["naturally_supported_by"]:
            if concern in top_concerns:
                already_helping.append(concern)

        roadmap_item = {
            "goal_label":          goal["label"],
            "goal_key":            goal_key,
            "is_blocked":          is_blocked,
            "blocking_reason":     blocking_reason,
            "roadmap_text":        goal["roadmap_text"],
            "phase3_ingredients":  goal["phase3_ingredients"],
            "already_helping":     already_helping,
        }

        roadmap.append(roadmap_item)

    return roadmap


# ───────────────────────────────────────────────────────────────────────────────
# HELPER — GOAL KEYS FOR FORM CHECKBOXES
#
# Returns a list of (key, label) pairs for rendering the goals form step.
# ───────────────────────────────────────────────────────────────────────────────

def get_goal_choices():
    """
    Returns a list of (key, label) pairs for rendering the goals form step.
    Loaded from database so admin can add/remove goals without code changes.
    """
    GOALS_DB = get_goals_db()
    choices = []
    for key, goal in GOALS_DB.items():
        choices.append({
            "key":   key,
            "label": goal["label"],
        })
    return choices
