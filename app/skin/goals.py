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

GOALS_DB = {

    "glow": {
        "label": "Natural Glow",
        "key": "glow",
        "requires_stable": ["sensitivity", "barrier_damage_acne"],
        "phase3_ingredients": ["Vitamin C 10%", "Niacinamide 5%", "AHA exfoliant (Lactic Acid 5%)"],
        "roadmap_text": (
            "A natural glow comes from good hydration, regular gentle exfoliation, and antioxidant protection. "
            "Your routine already starts building this from Phase 1 with barrier repair and hydration. "
            "In Phase 3, Vitamin C and gentle exfoliation are added to amplify the glow effect."
        ),
        "naturally_supported_by": ["dullness", "dehydration"],
    },

    "glass_skin": {
        "label": "Glass Skin",
        "key": "glass_skin",
        "requires_stable": ["acne", "sensitivity", "barrier_damage_acne", "comedones"],
        "phase3_ingredients": [
            "Hyaluronic Acid (multi-layered)",
            "Snail Mucin or Centella serum",
            "Light sealing facial oil (Squalane)",
        ],
        "roadmap_text": (
            "Glass skin is the result of deep, consistent hydration and a completely intact skin barrier. "
            "It cannot be achieved over active acne or a compromised barrier — the surface texture will not be clear. "
            "Phase 1 and 2 build the barrier and clear congestion. "
            "Phase 3 introduces layered hydration and a sealing oil that creates the glass-like finish."
        ),
        "naturally_supported_by": ["dehydration", "dryness", "sensitivity"],
    },

    "pore_minimizing": {
        "label": "Smaller-Looking Pores",
        "key": "pore_minimizing",
        "requires_stable": ["acne"],
        "phase3_ingredients": ["Niacinamide 5-10%", "Salicylic Acid 0.5-1% (maintenance)"],
        "roadmap_text": (
            "Pore size is largely genetic but pores appear smaller when they are not congested with sebum. "
            "Niacinamide in Phase 2 already starts this process by regulating oil and reducing pore appearance. "
            "Phase 3 maintains this with a lower-dose BHA toner used twice a week as upkeep."
        ),
        "naturally_supported_by": ["oiliness", "comedones", "acne"],
    },

    "even_tone": {
        "label": "Even Skin Tone",
        "key": "even_tone",
        "requires_stable": ["sensitivity", "barrier_damage_acne"],
        "phase3_ingredients": ["Tranexamic Acid 3-5%", "Alpha Arbutin 2%", "Vitamin C 10%"],
        "roadmap_text": (
            "Even tone requires reducing melanin overproduction and clearing existing dark marks. "
            "SPF every morning is the most important step — without it, brightening ingredients cannot work. "
            "The brightening actives introduced in Phase 2 (for pigmentation concern) already serve this goal. "
            "Phase 3 can combine two brightening agents if the skin tolerates it."
        ),
        "naturally_supported_by": ["pigmentation", "dullness"],
    },

    "anti_aging": {
        "label": "Anti-Aging Prevention",
        "key": "anti_aging",
        "requires_stable": ["sensitivity"],
        "phase3_ingredients": ["Retinol 0.025% (start slow)", "Peptides", "Vitamin C 10%"],
        "roadmap_text": (
            "The best anti-aging step is SPF every single morning — this is already in your Phase 1 routine. "
            "In Phase 3, Retinol is introduced if your skin is stable and tolerating actives. "
            "Start at the lowest concentration (0.025%) twice a week and increase every 3 months. "
            "Peptides can be added alongside Retinol for collagen support."
        ),
        "naturally_supported_by": ["aging", "dullness", "pigmentation"],
    },

    "hydration_plump": {
        "label": "Plump and Hydrated Look",
        "key": "hydration_plump",
        "requires_stable": [],
        "phase3_ingredients": ["Hyaluronic Acid", "Glycerin", "Ceramides", "Squalane (PM)"],
        "roadmap_text": (
            "Plump hydrated skin starts in Phase 1 — the entire barrier repair phase is building this foundation. "
            "This goal has no blocking concerns. "
            "Phase 3 adds a sealing facial oil at night to lock hydration in and amplify the plump effect."
        ),
        "naturally_supported_by": ["dryness", "dehydration"],
    },

    "acne_scar_fade": {
        "label": "Fade Acne Scars and Marks",
        "key": "acne_scar_fade",
        "requires_stable": ["acne", "barrier_damage_acne"],
        "phase3_ingredients": ["Azelaic Acid 10%", "Alpha Arbutin 2%", "Niacinamide 5%"],
        "roadmap_text": (
            "Acne marks (post-inflammatory hyperpigmentation) fade naturally over time but can be accelerated. "
            "You cannot fade marks while new breakouts are still forming — the source must be controlled first. "
            "Phase 2 clears active acne. Phase 3 then targets the remaining marks with brightening actives."
        ),
        "naturally_supported_by": ["acne", "pigmentation"],
    },

    "oil_control": {
        "label": "Control Oiliness Throughout the Day",
        "key": "oil_control",
        "requires_stable": ["sensitivity"],
        "phase3_ingredients": ["Zinc PCA", "Niacinamide 10%", "Oil-free moisturizer with mattifying finish"],
        "roadmap_text": (
            "Long-term oil control is a result of consistent sebum regulation — not stripping the skin. "
            "Niacinamide in Phase 2 already begins this work. "
            "Phase 3 can introduce Zinc PCA alongside Niacinamide for stronger sebum regulation."
        ),
        "naturally_supported_by": ["oiliness", "acne", "comedones"],
    },
}


# ───────────────────────────────────────────────────────────────────────────────
# GOAL ROADMAP GENERATOR
#
# Takes the user's selected goals and their top_concerns.
# Returns a list of goal roadmap items.
# Each item tells the user:
#   - their goal
#   - whether it is blocked by a current concern
#   - if blocked — what needs to happen first and when
#   - if not blocked — how Phase 3 delivers it
#   - which Phase 2 ingredients already move toward this goal
# ───────────────────────────────────────────────────────────────────────────────

def build_goal_roadmap(selected_goals, top_concerns, conflict_detected):

    # If no goals selected, return empty list
    # The result page simply does not show the goals section
    if not selected_goals:
        return []

    roadmap = []

    for goal_key in selected_goals:

        # Skip if this goal is not in our database
        if goal_key not in GOALS_DB:
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
    choices = []
    for key, goal in GOALS_DB.items():
        choices.append({
            "key":   key,
            "label": goal["label"],
        })
    return choices
