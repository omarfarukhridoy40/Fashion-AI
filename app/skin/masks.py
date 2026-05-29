# ═══════════════════════════════════════════════════════════════════════════════
# masks.py — Face Mask Database and Selection Logic
#
# This file is completely separate from logic.py on purpose.
# It only handles masks — nothing else.
# The engine in logic.py calls get_mask_recommendations() at the end.
# ═══════════════════════════════════════════════════════════════════════════════

# =============================================================================
# MASK DATABASE — now loaded from PostgreSQL via db_access.py
#
# All mask records including ingredients and steps are stored in the database.
# Admin panel: /admin/skin_profile/facemask/
#
# The get_mask_recommendations() function below loads from database each call.
# Data is cached by db_access.py for 1 hour.
# =============================================================================

from .db_access import get_mask_db


UNSAFE_MASK_INGREDIENTS = [
    "Lemon juice (phototoxic and too acidic — pH of 2 damages skin barrier)",
    "Cinnamon (causes chemical burns and contact dermatitis)",
    "Apple cider vinegar undiluted (pH destroys acid mantle)",
    "Baking soda (pH 9 disrupts skin barrier and causes long-term damage)",
    "Toothpaste (contains SLS and menthol — both irritating)",
    "Hot water as a base (breaks down ingredients and increases irritation risk)",
    "Raw garlic directly on skin (can cause chemical burns)",
]


# ───────────────────────────────────────────────────────────────────────────────
# MASK SELECTION FUNCTION
#
# Takes the same data as the main engine.
# Returns up to 2 masks that match the user's:
#   - skin type
#   - top concerns
#   - skin states (to check avoid_if)
#
# Rules:
#   1. Never recommend a mask that is in the user's avoid_if list
#   2. Match at least one top concern
#   3. Match the user's skin type
#   4. If user has sensitivity state — only return safe_level="all" masks
#   5. Return maximum 2 masks
# ───────────────────────────────────────────────────────────────────────────────

def get_mask_recommendations(skin_type, top_concerns, skin_states):

    # Load masks from database (cached — fast after first load)
    MASK_DB = get_mask_db()

    # Build a flat list of things to avoid
    # This combines the skin states and the sensitivity concern
    things_to_avoid = []

    for state in skin_states:
        things_to_avoid.append(state["state"])

    if "sensitivity" in top_concerns:
        things_to_avoid.append("sensitivity")

    # Check if user has any sensitivity state — this restricts to safe_level="all" only
    user_has_sensitivity = False
    for state in skin_states:
        if state["state"] in ["Sensitized", "Compromised Barrier"]:
            user_has_sensitivity = True

    # Also check if sensitivity is a top concern
    if "sensitivity" in top_concerns:
        user_has_sensitivity = True

    # Go through every mask and score it
    scored_masks = []

    # Valid skin type strings — used to separate skin type checks from state name checks.
    # Issue 7 fix: avoid_if mixes skin type names and skin state names in one list.
    # Without this set, a new skin type string could accidentally match a state name,
    # or vice versa. The two checks are now explicit and separate.
    valid_skin_types = {"Oily", "Dry", "Combination", "Normal"}

    for mask in MASK_DB:

        # RULE 1: Skip if this mask should be avoided for this user
        mask_should_be_avoided = False
        for avoid_item in mask["avoid_if"]:
            # Check against skin states and sensitivity concern (state names)
            if avoid_item in things_to_avoid:
                mask_should_be_avoided = True
            # Check against skin type explicitly — only when avoid_item is a skin type string
            if avoid_item in valid_skin_types and avoid_item == skin_type:
                mask_should_be_avoided = True

        if mask_should_be_avoided:
            continue

        # RULE 2: If user has sensitivity — only allow safe_level="all" masks
        if user_has_sensitivity and mask["safe_level"] != "all":
            continue

        # RULE 3: Skin type must be in the mask's for_types list
        if skin_type not in mask["for_types"]:
            continue

        # RULE 4: Score the mask by how many top concerns it addresses
        # More matching concerns = higher score = more relevant mask
        concern_matches = 0
        for concern in top_concerns:
            if concern in mask["for_concerns"]:
                concern_matches += 1

        # Only include masks that match at least one concern
        if concern_matches == 0:
            continue

        scored_masks.append({
            "mask": mask,
            "score": concern_matches,
        })

    # Sort by score — highest relevance first
    scored_masks.sort(key=lambda x: x["score"], reverse=True)

    # Return the top 2 most relevant masks only
    # We pick 2 because users can alternate them across the week
    top_masks = []
    for item in scored_masks[:2]:
        top_masks.append(item["mask"])

    # Issue 8 fallback: if no mask matched (e.g. sensitivity state + dark_circles only),
    # return the Aloe Vera and Cucumber mask as a safe universal default.
    # It has safe_level="all", avoid_if=[], and suits every skin type.
    # NOTE: also add "dark_circles" to the Aloe mask's for_concerns in the database admin
    # so it gets scored correctly before reaching this fallback.
    if not top_masks:
        for mask in MASK_DB:
            if mask["name"] == "Aloe Vera and Cucumber Calm Mask":
                top_masks.append(mask)
                break

    return top_masks
