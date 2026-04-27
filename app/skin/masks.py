# ═══════════════════════════════════════════════════════════════════════════════
# masks.py — Face Mask Database and Selection Logic
#
# This file is completely separate from logic.py on purpose.
# It only handles masks — nothing else.
# The engine in logic.py calls get_mask_recommendations() at the end.
# ═══════════════════════════════════════════════════════════════════════════════


# ───────────────────────────────────────────────────────────────────────────────
# MASK DATABASE
#
# Each mask is a dictionary with these fields:
#   name         - what to call the mask
#   for_concerns - list of concerns this mask helps
#   for_types    - list of skin types this mask suits
#   avoid_if     - list of skin states or concerns where this mask is UNSAFE
#   ingredients  - list of ingredients with amounts
#   how_to_use   - step by step instructions as a list
#   frequency    - how often to use it per week
#   benefit      - one sentence about what it does
#   safe_level   - "all" means any skin, "normal_only" means not for sensitive
# ───────────────────────────────────────────────────────────────────────────────

MASK_DB = [

    # ── OILY AND ACNE MASKS ───────────────────────────────────────────────────

    {
        "name": "Multani Mitti Cooling Mask",
        "for_concerns": ["acne", "oiliness", "comedones"],
        "for_types": ["Oily", "Combination"],
        "avoid_if": ["Dry", "Dehydrated", "Sensitized", "Compromised Barrier", "sensitivity"],
        "ingredients": [
            "2 tablespoons Multani Mitti (Fuller's Earth)",
            "1 tablespoon rose water",
            "1 teaspoon aloe vera gel",
        ],
        "how_to_use": [
            "Mix all ingredients into a smooth paste.",
            "Apply a thin, even layer to clean dry skin.",
            "Leave on for 10 to 12 minutes — not until fully dry.",
            "Rinse with cool water using gentle circular motions.",
            "Follow immediately with moisturizer.",
        ],
        "frequency": "Once per week",
        "benefit": "Absorbs excess oil, unclogs pores, and cools inflamed acne skin.",
        "safe_level": "normal_only",
        "warning": "Do not leave until completely dry — over-drying damages the skin barrier.",
    },

    {
        "name": "Neem and Turmeric Anti-Acne Mask",
        "for_concerns": ["acne", "comedones", "pigmentation"],
        "for_types": ["Oily", "Combination", "Normal"],
        "avoid_if": ["Sensitized", "Compromised Barrier"],
        "ingredients": [
            "1 teaspoon neem powder or 4-5 fresh neem leaves ground to paste",
            "A tiny pinch of turmeric (less than 1/8 teaspoon — turmeric stains)",
            "1 tablespoon plain yogurt (no flavoring)",
        ],
        "how_to_use": [
            "Mix all ingredients until smooth.",
            "Apply to clean skin avoiding the eye area.",
            "Leave on for 10 minutes.",
            "Rinse thoroughly with lukewarm water.",
            "Follow with moisturizer.",
        ],
        "frequency": "Once per week",
        "benefit": "Neem kills acne-causing bacteria. Turmeric reduces redness. Yogurt lactic acid gently brightens.",
        "safe_level": "normal_only",
        "warning": "Use minimal turmeric — too much stains the skin yellow temporarily.",
    },

    # ── DRY AND DEHYDRATION MASKS ─────────────────────────────────────────────

    {
        "name": "Honey and Oat Hydration Mask",
        "for_concerns": ["dryness", "dehydration", "sensitivity", "dullness"],
        "for_types": ["Dry", "Normal", "Combination", "Oily"],
        "avoid_if": [],
        "ingredients": [
            "1 tablespoon raw honey (unprocessed)",
            "2 tablespoons finely ground oats (blend rolled oats into powder)",
            "1 teaspoon plain whole milk yogurt",
        ],
        "how_to_use": [
            "Mix ingredients into a thick paste.",
            "Apply to clean damp skin in a gentle circular motion.",
            "Leave on for 15 minutes.",
            "Rinse with cool to lukewarm water.",
            "Follow with your regular moisturizer.",
        ],
        "frequency": "Once or twice per week",
        "benefit": "Honey is a natural humectant that draws moisture into skin. Oats soothe irritation and strengthen barrier.",
        "safe_level": "all",
        "warning": "Do a small patch test if you have a honey or oat sensitivity.",
    },

    {
        "name": "Banana and Milk Nourishing Mask",
        "for_concerns": ["dryness", "dullness", "dehydration"],
        "for_types": ["Dry", "Normal"],
        "avoid_if": ["Oily"],
        "ingredients": [
            "Half a ripe banana, mashed smooth",
            "1 tablespoon full-fat milk",
            "1 teaspoon honey",
        ],
        "how_to_use": [
            "Mash banana until no lumps remain.",
            "Mix in milk and honey.",
            "Apply to clean skin.",
            "Leave on for 15 minutes.",
            "Rinse with cool water.",
        ],
        "frequency": "Once per week",
        "benefit": "Banana provides potassium and vitamins that soften dry skin. Milk lactic acid brightens gently.",
        "safe_level": "all",
        "warning": "Not suitable for oily skin — the banana sugars can feed bacteria on oily-prone skin.",
    },

    # ── BRIGHTENING AND PIGMENTATION MASKS ───────────────────────────────────

    {
        "name": "Potato and Rose Water Brightening Mask",
        "for_concerns": ["pigmentation", "dullness", "dark_circles"],
        "for_types": ["Oily", "Combination", "Normal", "Dry"],
        "avoid_if": ["Sensitized"],
        "ingredients": [
            "2 tablespoons fresh potato juice (grate a small raw potato and squeeze the juice)",
            "1 tablespoon rose water",
            "1 teaspoon aloe vera gel",
        ],
        "how_to_use": [
            "Grate a small raw potato and press through a cloth to extract the juice.",
            "Mix potato juice, rose water and aloe vera together.",
            "Apply to clean skin or under-eye area with a cotton pad.",
            "Leave on for 15 minutes.",
            "Rinse with cool water.",
        ],
        "frequency": "Twice per week",
        "benefit": "Potato contains natural catecholase enzyme which gently brightens dark spots and uneven tone.",
        "safe_level": "all",
        "warning": "Use fresh potato juice only — do not store it. Results take 4 to 6 weeks of consistent use.",
    },

    {
        "name": "Tomato and Sandalwood Glow Mask",
        "for_concerns": ["pigmentation", "dullness", "oiliness"],
        "for_types": ["Oily", "Combination", "Normal"],
        "avoid_if": ["Sensitized", "Dry", "Dehydrated"],
        "ingredients": [
            "1 tablespoon fresh tomato pulp (scoop from inside a ripe tomato)",
            "1 teaspoon sandalwood powder",
            "A few drops of rose water to adjust consistency",
        ],
        "how_to_use": [
            "Mix tomato pulp and sandalwood powder into a paste.",
            "Add rose water drops to reach a spreadable consistency.",
            "Apply to clean skin.",
            "Leave on for 10 minutes.",
            "Rinse with cool water.",
        ],
        "frequency": "Once per week",
        "benefit": "Tomato lycopene is an antioxidant that fights sun damage. Sandalwood soothes and brightens.",
        "safe_level": "normal_only",
        "warning": "Do not use before sun exposure — apply at night or indoors only.",
    },

    # ── SOOTHING AND SENSITIVITY MASKS ───────────────────────────────────────

    {
        "name": "Aloe Vera and Cucumber Calm Mask",
        "for_concerns": ["sensitivity", "dryness", "dehydration", "dullness"],
        "for_types": ["Oily", "Combination", "Normal", "Dry"],
        "avoid_if": [],
        "ingredients": [
            "2 tablespoons fresh aloe vera gel (from the plant leaf if possible)",
            "1 tablespoon fresh cucumber juice (grate and squeeze)",
            "1 teaspoon plain cold yogurt",
        ],
        "how_to_use": [
            "Extract fresh aloe gel from a leaf or use pure store-bought gel.",
            "Grate cucumber and press to extract juice.",
            "Mix all three ingredients.",
            "Apply to clean skin.",
            "Leave on for 15 to 20 minutes.",
            "Rinse with cool water.",
        ],
        "frequency": "Twice per week",
        "benefit": "Aloe vera reduces redness and repairs the skin barrier. Cucumber cools and reduces inflammation.",
        "safe_level": "all",
        "warning": "This is the safest mask in the list — suitable even for reactive and sensitive skin.",
    },

    # ── ANTI-AGING MASKS ─────────────────────────────────────────────────────

    {
        "name": "Egg White and Honey Firming Mask",
        "for_concerns": ["aging", "oiliness", "dullness"],
        "for_types": ["Oily", "Normal", "Combination"],
        "avoid_if": ["Sensitized", "Dry"],
        "ingredients": [
            "1 egg white (separate from yolk carefully)",
            "1 teaspoon raw honey",
            "A few drops of lemon juice — SKIP THIS if you have any sensitivity",
        ],
        "how_to_use": [
            "Whisk egg white until slightly foamy.",
            "Mix in honey.",
            "Apply to clean skin in upward strokes.",
            "Leave on for 15 minutes — the mask will feel tight as it dries.",
            "Rinse thoroughly with lukewarm water.",
        ],
        "frequency": "Once per week",
        "benefit": "Egg white temporarily tightens pores and firms skin. Honey moisturizes and adds antioxidants.",
        "safe_level": "normal_only",
        "warning": "Omit lemon juice completely if your skin is reactive. Skip if you have egg allergy.",
    },

    {
        "name": "Oat and Yogurt Anti-Aging Mask",
        "for_concerns": ["aging", "dryness", "dullness", "sensitivity"],
        "for_types": ["Dry", "Normal", "Combination"],
        "avoid_if": [],
        "ingredients": [
            "2 tablespoons finely ground oats",
            "2 tablespoons plain full-fat yogurt",
            "1 teaspoon raw honey",
        ],
        "how_to_use": [
            "Mix all ingredients to a smooth paste.",
            "Apply to clean skin.",
            "Leave on for 15 minutes.",
            "Rinse gently with cool water.",
            "Follow with moisturizer.",
        ],
        "frequency": "Once or twice per week",
        "benefit": "Yogurt lactic acid gently resurfaces without irritation. Oats soothe while building barrier strength.",
        "safe_level": "all",
        "warning": "The gentlest anti-aging mask option — suitable for mature sensitive skin.",
    },
]


# ───────────────────────────────────────────────────────────────────────────────
# UNSAFE INGREDIENTS TO NEVER INCLUDE IN ANY HOMEMADE MASK
#
# This is a reference list. The masks above are already designed to exclude
# these. This list is here for documentation and future validation.
# ───────────────────────────────────────────────────────────────────────────────

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

    for mask in MASK_DB:

        # RULE 1: Skip if this mask should be avoided for this user
        mask_should_be_avoided = False
        for avoid_item in mask["avoid_if"]:
            if avoid_item in things_to_avoid:
                mask_should_be_avoided = True
            if avoid_item == skin_type:
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

    return top_masks
