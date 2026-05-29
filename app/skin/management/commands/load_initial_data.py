from django.core.management.base import BaseCommand

from skin.db_access import clear_all_caches
from skin.models import (
    AvoidIngredient,
    ConcernTimeline,
    ConflictPair,
    FaceMask,
    FaceMaskIngredient,
    FaceMaskStep,
    Ingredient,
    NextGoal,
    PlainTextKeyword,
    SkinGoal,
    SkinGoalIngredient,
)


# Initial content lives in this command on purpose. Do not import these values
# from logic.py, masks.py, or goals.py because those modules now read from the DB.
INGREDIENT_DB = {
    "niacinamide": {
        "label": "Niacinamide 5%",
        "targets": ["acne", "oiliness", "dullness", "pigmentation", "comedones", "sensitivity"],
        "why": "Regulates sebum and controls oiliness, reduces pore appearance, calms redness and inflammation, brightens dull skin, and fades pigmentation — safe across all skin states including sensitive and reactive skin",
        "sensitivity_safe": True, "dehydrated_safe": True,
        "phase_min": 2, "product_type": "serum", "time": "AM/PM",
    },
    "salicylic_acid": {
        "label": "Salicylic Acid 1-2%",
        "targets": ["acne", "comedones", "oiliness"],
        "why": "Oil-soluble acid that penetrates pores and dissolves sebum plugs — gold standard for acne and blackheads",
        "sensitivity_safe": False, "dehydrated_safe": False,
        "phase_min": 3, "product_type": "toner/cleanser", "time": "PM",
    },
    "hyaluronic_acid": {
        "label": "Hyaluronic Acid",
        "targets": ["dryness", "dullness", "dehydration"],
        "why": "Pulls water into the skin and holds it — essential for any dehydration state regardless of skin type",
        "sensitivity_safe": True, "dehydrated_safe": True,
        "phase_min": 1, "product_type": "serum", "time": "AM/PM",
    },
    "ceramides": {
        "label": "Ceramides",
        "targets": ["dryness", "sensitivity", "barrier_damage"],
        "why": "Structural lipids that rebuild the skin barrier — the foundation of all barrier repair routines",
        "sensitivity_safe": True, "dehydrated_safe": True,
        "phase_min": 1, "product_type": "moisturizer", "time": "AM/PM",
    },
    "centella": {
        "label": "Centella Asiatica (Cica)",
        "targets": ["sensitivity", "barrier_damage", "acne", "redness"],
        "why": "Anti-inflammatory herb that calms reactive skin and accelerates barrier repair — widely available in BD market",
        "sensitivity_safe": True, "dehydrated_safe": True,
        "phase_min": 1, "product_type": "serum/cream", "time": "AM/PM",
    },
    "panthenol": {
        "label": "Panthenol (Vitamin B5)",
        "targets": ["sensitivity", "dryness", "barrier_damage"],
        "why": "Draws moisture into skin and supports barrier healing — ideal Phase 1 ingredient for all conflict routines",
        "sensitivity_safe": True, "dehydrated_safe": True,
        "phase_min": 1, "product_type": "serum/moisturizer", "time": "AM/PM",
    },
    "vitamin_c": {
        "label": "Vitamin C 10%",   # FIX: capped at 10% — 15% is too aggressive even at intermediate level
        "targets": ["dullness", "pigmentation", "aging"],
        "why": "Antioxidant that inhibits melanin and boosts collagen — most effective brightener for sun-damaged skin",
        "sensitivity_safe": False, "dehydrated_safe": False,
        "phase_min": 3, "product_type": "serum", "time": "AM",
    },
    "alpha_arbutin": {
        "label": "Alpha Arbutin 2%",
        "targets": ["pigmentation", "dark_spots"],
        "why": "Gentle melanin inhibitor — slower than Vitamin C but safe for sensitive skin",
        "sensitivity_safe": True, "dehydrated_safe": True,
        "phase_min": 2, "product_type": "serum", "time": "PM",
    },
    "azelaic_acid": {
        "label": "Azelaic Acid 10%",
        "targets": ["acne", "pigmentation", "redness", "barrier_damage_acne"],
        "why": "Unique dual-action: treats acne AND fades marks while being gentle for sensitive and dry skin — the hero conflict ingredient",
        "sensitivity_safe": True, "dehydrated_safe": True,
        "phase_min": 3, "product_type": "serum/gel", "time": "PM",
    },
    "tranexamic_acid": {
        "label": "Tranexamic Acid 3-5%",
        "targets": ["pigmentation", "melasma", "dark_spots"],
        "why": "Highly effective for melanin overproduction from sun damage — particularly relevant for Bangladesh skin tones",
        "sensitivity_safe": True, "dehydrated_safe": True,
        "phase_min": 2, "product_type": "serum", "time": "AM/PM",
    },
    "zinc_pca": {
        "label": "Zinc PCA",
        "targets": ["oiliness", "acne", "comedones"],
        "why": "Regulates sebaceous gland activity without drying — ideal for dehydrated oily skin",
        "sensitivity_safe": True, "dehydrated_safe": True,
        "phase_min": 2, "product_type": "serum/toner", "time": "AM/PM",
    },
    "glycerin": {
        "label": "Glycerin",
        "targets": ["dryness", "dehydration", "dullness"],
        "why": "The most universally safe humectant — safe for all skin types, states, and ages",
        "sensitivity_safe": True, "dehydrated_safe": True,
        "phase_min": 1, "product_type": "all", "time": "AM/PM",
    },
    "caffeine": {
        "label": "Caffeine Extract",
        "targets": ["dark_circles", "puffiness"],
        "why": "Constricts blood vessels under thin eye skin, reducing dark circles and puffiness — apply cold for best effect",
        "sensitivity_safe": True, "dehydrated_safe": True,
        "phase_min": 2, "product_type": "eye cream", "time": "AM",
    },
    "retinol": {
        "label": "Retinol 0.025-0.5%",
        "targets": ["aging", "acne", "pigmentation", "dullness"],
        "why": "Accelerates cell turnover and stimulates collagen — most evidence-backed anti-aging ingredient, requires careful introduction",
        "sensitivity_safe": False, "dehydrated_safe": False,
        "phase_min": 3, "product_type": "serum/cream", "time": "PM",
    },
    "peptides": {
        "label": "Peptides",
        "targets": ["aging", "firmness"],
        "why": "Signal proteins that stimulate collagen production — gentle enough for sensitive skin, effective for 28+ age group",
        "sensitivity_safe": True, "dehydrated_safe": True,
        "phase_min": 2, "product_type": "serum/moisturizer", "time": "AM/PM",
    },
    "squalane": {
        "label": "Squalane",
        "targets": ["dryness", "barrier_damage", "dehydration"],
        "why": "Lightweight non-comedogenic oil that mimics skin's natural lipids — uniquely safe for dry AND acne-prone skin",
        "sensitivity_safe": True, "dehydrated_safe": True,
        "phase_min": 1, "product_type": "oil/moisturizer", "time": "PM",
    },
    # FIX: added Lactic Acid — gentler exfoliant for dry skin users who need cell turnover
    # Referenced in NEXT_GOALS for pigmentation but was missing from DB so could never be recommended
    "lactic_acid": {
        "label": "Lactic Acid 5%",
        "targets": ["dullness", "dryness", "pigmentation", "comedones"],
        "why": "Gentler AHA exfoliant — larger molecule than glycolic acid, so less irritating. Safe for dry skin types that cannot tolerate salicylic acid.",
        "sensitivity_safe": False, "dehydrated_safe": False,
        "phase_min": 3, "product_type": "toner/serum", "time": "PM",
    },
}

CONCERN_TIMELINES = {
    "acne":               {"weeks": "4-6",   "popup": "Acne usually starts improving in 4-6 weeks. Your skin may look slightly worse in weeks 1-2 — this is normal purging. The active is accelerating cell turnover and pushing congestion to the surface. Do not stop.", "purge_warning": True},
    "barrier_damage_acne": {"weeks": "6-8",   "popup": "Barrier-damage driven acne responds slower. Focus on barrier repair first — breakouts reduce as the barrier heals. Expect 6-8 weeks.", "purge_warning": False},
    "pigmentation":       {"weeks": "8-12",  "popup": "Dark spots are the slowest concern — 8-12 weeks minimum. Daily SPF is non-negotiable. Without SPF, brightening actives cannot work.", "purge_warning": False},
    "dullness":           {"weeks": "2-3",   "popup": "Dullness is the fastest win — most users notice visible glow within 2-3 weeks of consistent routine use.", "purge_warning": False},
    "dryness":            {"weeks": "2-4",   "popup": "Barrier repair takes 2-4 weeks of gentle, consistent care. Introduce no new products during this window.", "purge_warning": False},
    "sensitivity":        {"weeks": "4-6",   "popup": "Sensitized skin needs full 4-6 weeks of gentle routine before any active is introduced. No experiments.", "purge_warning": False},
    "dehydration":        {"weeks": "1-2",   "popup": "Dehydration is the fastest to fix — most users feel a difference within 1-2 weeks of consistent hydration layering.", "purge_warning": False},
    "oiliness":           {"weeks": "4-6",   "popup": "Oil control improves over 4-6 weeks. Do not over-cleanse — stripping oil makes the skin overproduce more.", "purge_warning": False},
    "dark_circles":       {"weeks": "6-8",   "popup": "Dark circles take 6-8 weeks of consistent treatment. Apply eye cream cold, morning and night.", "purge_warning": False},
    "comedones":          {"weeks": "4-6",   "popup": "Blackheads and whiteheads clear gradually over 4-6 weeks. Never squeeze — it pushes bacteria deeper.", "purge_warning": False},
    "aging":              {"weeks": "12+",   "popup": "Anti-aging is a long game — real visible results take 12+ weeks. Retinol in particular needs 3 months before judging.", "purge_warning": True},
}

CONFLICT_PAIRS = [
    ("acne", "dryness"),
    ("acne", "sensitivity"),
    ("sensitivity", "pigmentation"),
    ("dryness", "pigmentation"),
]

AVOID_MAP = {
    "acne":               ["Coconut oil", "Heavy cream moisturizers", "Isopropyl myristate", "Lanolin"],
    "sensitivity":        ["Alcohol denat", "Synthetic fragrance", "Essential oils (lemon, peppermint)", "Physical scrubs"],
    "dryness":            ["SLS foaming cleansers", "Alcohol denat", "Daily clay masks", "Over-exfoliation"],
    "oiliness":           ["Heavy facial oils", "Thick occlusive creams (shea-heavy)"],
    "pigmentation":       ["Citrus oils on skin (phototoxic)", "Photosensitizing actives without SPF"],
    "dehydration":        ["Alcohol-based toners", "Skipping moisturizer to control oil"],
    "barrier_damage_acne": ["Benzoyl peroxide (high%)", "Strong exfoliating acids", "SLS cleansers"],
    "aging":              ["Skipping SPF", "High-fragrance products", "Physical scrubs on mature skin"],
}

PLAIN_TEXT_KEYWORDS = {
    "acne":           ["pimple", "pimples", "acne", "breakout", "breakouts", "zit", "zits", "blemish", "spot"],
    "pigmentation":   ["dark spot", "dark spots", "patch", "patches", "uneven", "discoloration", "mark", "marks", "scar", "melasma"],
    "dullness":       ["dull", "tired", "glow", "bright", "brightness", "radiance", "flat", "lifeless"],
    "dryness":        ["dry", "tight", "flaky", "flaking", "rough", "peeling", "peel"],
    "oiliness":       ["oily", "greasy", "shine", "shiny", "sebum"],
    "sensitivity":    ["sensitive", "react", "reaction", "burn", "burning", "sting", "itch", "itchy", "red", "redness", "irritat"],
    "dark_circles":   ["dark circle", "dark circles", "under eye", "eye bag", "eye bags", "tired eyes"],
    "comedones":      ["blackhead", "blackheads", "whitehead", "whiteheads", "clogged pore", "pore"],
    "aging":          ["wrinkle", "wrinkles", "fine line", "fine lines", "aging", "ageing", "sagging", "collagen"],
    "dehydration":    ["dehydrat", "lacks moisture", "thirsty skin"],
}

NEXT_GOALS = {
    "acne":               "Once breakouts are controlled (week 4-6), your next goal is fading post-acne dark marks with Alpha Arbutin or Azelaic Acid.",
    "barrier_damage_acne": "After barrier repair (week 6-8), reassess whether acne persists. Many barrier-damage breakouts resolve on their own.",
    "pigmentation":       "After 8 weeks of brightening, introduce gentle exfoliation (Lactic Acid 5%) to accelerate cell turnover.",
    "dullness":           "After glow is established (week 3), add antioxidant protection and consider an SPF upgrade.",
    "dryness":            "After barrier is repaired (week 4), gradually introduce Niacinamide — the safest first active.",
    "sensitivity":        "After 6 weeks of barrier repair, begin Niacinamide 2% to build tolerance slowly.",
    "dehydration":        "After hydration improves (week 2), assess remaining concerns — oiliness often reduces once dehydration resolves.",
    "oiliness":           "After oil control improves, evaluate whether acne or pigmentation needs targeting next.",
    "dark_circles":       "After 6-8 weeks of caffeine treatment, add Retinol eye cream for deeper discoloration.",
    "comedones":          "After comedones clear, switch to a maintenance BHA toner 2x per week to prevent recurrence.",
    "aging":              "After 3 months on Retinol, step up concentration every 3 months (0.025% to 0.05% to 0.1%).",
}

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


class Command(BaseCommand):
    help = "Load initial skin data from Python dictionaries into the database."

    def handle(self, *args, **options):
        self.stdout.write("Loading initial skin data...")

        self._load_ingredients()
        self._load_timelines()
        self._load_conflict_pairs()
        self._load_avoid_map()
        self._load_keywords()
        self._load_next_goals()
        self._load_masks()
        self._load_goals()

        clear_all_caches()
        self.stdout.write(self.style.SUCCESS("Done. Verify at /admin/."))

    def _load_ingredients(self):
        created = skipped = 0
        for key, data in INGREDIENT_DB.items():
            _, was_created = Ingredient.objects.get_or_create(
                key=key,
                defaults={
                    "label": data["label"],
                    "why": data["why"],
                    "targets": ",".join(data["targets"]),
                    "sensitivity_safe": data["sensitivity_safe"],
                    "dehydrated_safe": data["dehydrated_safe"],
                    "phase_min": data["phase_min"],
                    "product_type": data["product_type"],
                    "time": data["time"],
                },
            )
            created, skipped = self._count(created, skipped, was_created)
        self.stdout.write(
            f"  Ingredients: {created} created, {skipped} skipped"
        )

    def _load_timelines(self):
        created = skipped = 0
        for key, data in CONCERN_TIMELINES.items():
            _, was_created = ConcernTimeline.objects.get_or_create(
                concern_key=key,
                defaults={
                    "weeks": data["weeks"],
                    "popup_text": data["popup"],
                    "purge_warning": data["purge_warning"],
                },
            )
            created, skipped = self._count(created, skipped, was_created)
        self.stdout.write(
            f"  Concern Timelines: {created} created, {skipped} skipped"
        )

    def _load_conflict_pairs(self):
        created = skipped = 0
        for concern_a, concern_b in CONFLICT_PAIRS:
            _, was_created = ConflictPair.objects.get_or_create(
                concern_a=concern_a,
                concern_b=concern_b,
            )
            created, skipped = self._count(created, skipped, was_created)
        self.stdout.write(
            f"  Conflict Pairs: {created} created, {skipped} skipped"
        )

    def _load_avoid_map(self):
        created = skipped = 0
        for concern_key, items in AVOID_MAP.items():
            for ingredient_name in items:
                _, was_created = AvoidIngredient.objects.get_or_create(
                    concern_key=concern_key,
                    ingredient_name=ingredient_name,
                )
                created, skipped = self._count(created, skipped, was_created)
        self.stdout.write(
            f"  Avoid Ingredients: {created} created, {skipped} skipped"
        )

    def _load_keywords(self):
        created = skipped = 0
        for concern_key, keywords in PLAIN_TEXT_KEYWORDS.items():
            for keyword in keywords:
                _, was_created = PlainTextKeyword.objects.get_or_create(
                    concern_key=concern_key,
                    keyword=keyword,
                )
                created, skipped = self._count(created, skipped, was_created)
        self.stdout.write(
            f"  Plain Text Keywords: {created} created, {skipped} skipped"
        )

    def _load_next_goals(self):
        created = skipped = 0
        for concern_key, goal_text in NEXT_GOALS.items():
            _, was_created = NextGoal.objects.get_or_create(
                concern_key=concern_key,
                defaults={"goal_text": goal_text},
            )
            created, skipped = self._count(created, skipped, was_created)
        self.stdout.write(f"  Next Goals: {created} created, {skipped} skipped")

    def _load_masks(self):
        created = skipped = 0
        for mask_data in MASK_DB:
            mask, was_created = FaceMask.objects.get_or_create(
                name=mask_data["name"],
                defaults={
                    "benefit": mask_data["benefit"],
                    "frequency": mask_data["frequency"],
                    "warning": mask_data.get("warning", ""),
                    "for_types": ",".join(mask_data["for_types"]),
                    "for_concerns": ",".join(mask_data["for_concerns"]),
                    "avoid_if": ",".join(mask_data["avoid_if"]),
                    "safe_level": mask_data["safe_level"],
                },
            )
            if was_created:
                self._create_mask_children(mask, mask_data)
            created, skipped = self._count(created, skipped, was_created)
        self.stdout.write(f"  Face Masks: {created} created, {skipped} skipped")

    def _load_goals(self):
        created = skipped = 0
        for goal_key, goal_data in GOALS_DB.items():
            goal, was_created = SkinGoal.objects.get_or_create(
                key=goal_key,
                defaults={
                    "label": goal_data["label"],
                    "roadmap_text": goal_data["roadmap_text"],
                    "requires_stable": ",".join(
                        goal_data["requires_stable"]
                    ),
                    "naturally_supported_by": ",".join(
                        goal_data["naturally_supported_by"]
                    ),
                },
            )
            if was_created:
                self._create_goal_children(goal, goal_data)
            created, skipped = self._count(created, skipped, was_created)
        self.stdout.write(f"  Skin Goals: {created} created, {skipped} skipped")

    @staticmethod
    def _create_mask_children(mask, mask_data):
        for order, text in enumerate(mask_data["ingredients"]):
            FaceMaskIngredient.objects.create(
                mask=mask,
                text=text,
                order=order,
            )
        for order, text in enumerate(mask_data["how_to_use"]):
            FaceMaskStep.objects.create(mask=mask, text=text, order=order)

    @staticmethod
    def _create_goal_children(goal, goal_data):
        for order, text in enumerate(goal_data["phase3_ingredients"]):
            SkinGoalIngredient.objects.create(
                goal=goal,
                text=text,
                order=order,
            )

    @staticmethod
    def _count(created, skipped, was_created):
        if was_created:
            return created + 1, skipped
        return created, skipped + 1
