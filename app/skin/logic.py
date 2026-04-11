# ═══════════════════════════════════════════════════════════════════════════════
# logic.py — Production-Level Skin Analysis Engine
# ═══════════════════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────────────────
# SIGNAL WEIGHTS
# ───────────────────────────────────────────────────────────────────────────────
SIGNAL_WEIGHTS = {
    "after_hours":  3,
    "after_wash":   2,
    "pores":        2,
    "flaky":        2,
    "reaction":     3,
    "sleep":        1,
    "user_select":  3,
    "plain_text":   2,
    "age_signal":   2,
}

# ───────────────────────────────────────────────────────────────────────────────
# INGREDIENT DATABASE
# ───────────────────────────────────────────────────────────────────────────────
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

# ───────────────────────────────────────────────────────────────────────────────
# CONCERN TIMELINES
# ───────────────────────────────────────────────────────────────────────────────
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


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY
# ═══════════════════════════════════════════════════════════════════════════════
def _get_list(data, key):
    if hasattr(data, 'getlist'):
        return data.getlist(key)
    val = data.get(key, [])
    return val if isinstance(val, list) else ([val] if val else [])


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 0 — INPUT VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════
def validate_minimum_data(data):
    required = ["after_wash", "after_hours"]
    recommended = ["pores", "flaky", "reaction", "experience", "sleep", "age_group"]
    missing_required = [f for f in required if not data.get(f)]
    missing_recommended = [f for f in recommended if not data.get(f)]
    if missing_required:
        return False, missing_required, None, 0
    defaults = {
        "pores": "visible", "flaky": "sometimes", "reaction": "slight",
        "experience": "basic", "sleep": "6-7", "age_group": "adult_25_35",
        "concerns": [], "sun_exposure": "medium_sun",
    }
    filled = dict(data) if not hasattr(data, '_mutable') else data
    if hasattr(filled, '_mutable'):
        filled = dict(filled)
    for field in missing_recommended:
        if not filled.get(field):
            filled[field] = defaults.get(field, "")
    confidence_penalty = len(missing_recommended) * 5
    return True, missing_recommended, filled, confidence_penalty


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — PLAIN TEXT EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════
def extract_plain_text_signals(plain_text):
    if not plain_text:
        return {}, []
    text = plain_text.lower()
    detected = {}
    matched = []
    for concern, keywords in PLAIN_TEXT_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                detected[concern] = detected.get(concern, 0) + 1
                matched.append({"keyword": kw, "maps_to": concern})
    return detected, matched


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — SKIN STATE DETECTION
# ═══════════════════════════════════════════════════════════════════════════════
def detect_skin_states(data, oil_score, dry_score):
    states = []
    after_wash = data.get("after_wash", "")
    after_hours = data.get("after_hours", "")
    reaction = data.get("reaction", "")
    experience = data.get("experience", "")
    pores = data.get("pores", "")
    flaky = data.get("flaky", "")

    # DEHYDRATED OILY — tight after wash + oily later
    if after_wash == "tight" and after_hours in ["very_oily", "oily_tzone"]:
        states.append({
            "state": "Dehydrated",
            "reason": "Tight right after washing but oily within hours — classic dehydrated oily skin. Your skin lacks water and overproduces oil to compensate. These are two separate systems.",
            "priority": 1,
        })
    elif after_wash == "tight" and after_hours == "dry" and oil_score == 0:
        states.append({
            "state": "Dehydrated",
            "reason": "Persistently tight and dry — water content is low across the board. Humectants come first.",
            "priority": 1,
        })
    elif after_wash == "tight" and after_hours == "normal":
        # GAP 3 FIX: tight + normalizes = Mild Dehydration Tendency.
        # Skin loses surface water right after washing but self-regulates within hours.
        # This is not full dehydration but the user needs to know about it — a humectant
        # applied to damp skin within 60 seconds prevents the water loss.
        states.append({
            "state": "Mild Dehydration Tendency",
            "reason": "Tight right after washing but normalizes within hours — your skin loses surface water immediately after cleansing but self-regulates. Apply a humectant serum (Hyaluronic Acid or Glycerin) to damp skin within 60 seconds of washing to lock in that water before it evaporates.",
            "priority": 2,
        })

    # SENSITIZED — acquired vs genetic
    if reaction == "burning" and experience in ["intermediate", "advanced"]:
        states.append({
            "state": "Sensitized",
            "reason": "Strong reactions combined with an existing product routine suggests acquired sensitivity — likely from over-exfoliation or product overload. This is reversible.",
            "priority": 1,
        })
    elif reaction == "burning":
        states.append({
            "state": "Sensitized",
            "reason": "Burning and stinging indicate a compromised barrier. Barrier repair is the first priority before anything else.",
            "priority": 1,
        })

    # CONGESTED
    if pores in ["visible", "very_visible"] and after_hours in ["oily_tzone", "very_oily"]:
        states.append({
            "state": "Congested",
            "reason": "Visible pores combined with persistent oiliness indicates active congestion — sebum is not clearing efficiently from pores.",
            "priority": 2,
        })

    # COMPROMISED BARRIER
    # FIX: seasonal flaking is NOT a barrier signal — only chronic flaking counts
    if flaky == "yes_often" and reaction in ["redness", "burning", "slight"]:
        states.append({
            "state": "Compromised Barrier",
            "reason": "Flaking combined with reactive skin strongly indicates a damaged moisture barrier — the root cause of many secondary concerns.",
            "priority": 1,
        })

    return states


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 — SKIN TYPE
# ═══════════════════════════════════════════════════════════════════════════════
def calculate_skin_type(data):
    oil = 0
    dry = 0
    after_wash = data.get("after_wash", "")
    after_hours = data.get("after_hours", "")
    pores = data.get("pores", "")
    flaky = data.get("flaky", "")

    if after_wash == "tight":
        dry += SIGNAL_WEIGHTS["after_wash"]
    elif after_wash == "oily":
        oil += SIGNAL_WEIGHTS["after_wash"]

    if after_hours == "dry":
        dry += SIGNAL_WEIGHTS["after_hours"]        # +3 — strong dry signal
    elif after_hours == "oily_tzone":
        # GAP 1 FIX: reduce from 3 to 2. oily_tzone = T-zone only shiny.
        # It is NOT the same clinical signal as very_oily (whole face shiny).
        # Using weight 3 was treating "forehead shiny" the same as "entirely oily face".
        oil += 2
        dry += 1                                    # cheeks may be drier — keep
    elif after_hours == "very_oily":
        oil += SIGNAL_WEIGHTS["after_hours"]        # +3 — full-face oiliness
    elif after_hours == "normal":
        # GAP 2/5 FIX: after_hours=normal means skin self-regulates.
        # Set a minimum floor of 2 for both scores AFTER all other scoring.
        # This is applied at the end of scoring — see below the pores/flaky section.
        pass  # handled after pores and flaky scoring

    if pores == "very_visible":
        oil += SIGNAL_WEIGHTS["pores"]
    elif pores == "visible":
        oil += 1
    # FIX: pores=not_visible removed — not having visible pores does NOT mean dry skin.
    # Many oily skin people have smaller or normal-sized pores. This was pushing 36 users
    # toward Combination incorrectly.

    # FIX: Flaky signal is only meaningful when oil signals are weak.
    # In Bangladesh, December-February causes temporary flaking in oily-skinned users.
    # If oil >= 3, the skin is producing significant sebum — flaky=sometimes is seasonal
    # noise, and flaky=yes_often is biologically impossible with strong oiliness.
    # Only apply flaky signal when oil score is low (genuine dry signal).
    # FIX: "seasonal" is a new option that explicitly means winter-only flaking —
    # treated as "no" (same as ignoring it) regardless of oil level.
    if flaky != "seasonal" and oil < 3:
        if flaky == "yes_often":
            dry += SIGNAL_WEIGHTS["flaky"]   # +2 — genuine dry indicator
        elif flaky == "sometimes":
            dry += 1                         # +1 — mild dry signal
    # else: oil >= 3 or seasonal → ignore flaky entirely

    # ── DEHYDRATED OILY OVERRIDE ──────────────────────────────────────────────
    # Must run BEFORE the normalization guards below.
    # tight + oily later = dehydrated oily — never Combination.
    if after_wash == "tight" and after_hours in ["very_oily", "oily_tzone"]:
        return "Oily", oil, dry

    # ── NORMALIZATION GUARDS (Gaps 1, 2, 4, 5) ───────────────────────────────

    # Gap 2/5 Guard: after_hours=normal means skin self-regulates.
    # Applied AFTER all scoring so it overrides any dry or oil cascade from
    # pores and flaky. Floor of 2 on both ensures neither the pure-Dry nor
    # pure-Oily rule can fire when the primary signal (after_hours) is normal.
    if after_hours == "normal":
        oil = max(oil, 2)
        dry = max(dry, 2)

    # Gap 1 Guard: oily_tzone with non-tight wash = definitionally Combination.
    # T-zone oiliness means NOT all the face is oily — Combination by definition.
    # (tight + oily_tzone is caught above by the dehydrated oily override.)
    if after_hours == "oily_tzone" and after_wash in ["normal", "oily"]:
        return "Combination", oil, dry

    # Gap 4 Guard: after_hours=dry is the strongest dry signal possible.
    # If dry score is dominant (>=5), pore visibility should not override it.
    # Very visible pores in a dry person = dehydrated dry skin — still Dry.
    if after_hours == "dry" and after_wash in ["tight", "normal"] and dry >= 5:
        return "Dry", oil, dry

    # ── FINAL CLASSIFICATION ──────────────────────────────────────────────────
    if oil >= 4 and dry <= 1:
        skin_type = "Oily"
    elif oil >= 5 and dry <= 2:
        skin_type = "Oily"
    elif dry >= 4 and oil <= 1:
        skin_type = "Dry"
    elif oil >= 2 and dry >= 2:
        skin_type = "Combination"
    elif oil >= 3:
        skin_type = "Oily"
    elif dry >= 3:
        skin_type = "Dry"
    else:
        skin_type = "Combination"

    return skin_type, oil, dry


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4 — CONCERN SCORING
# ═══════════════════════════════════════════════════════════════════════════════
def calculate_concerns(data, skin_type, skin_states, oil_score, dry_score, plain_text_signals, age_group):
    scores = {
        "acne": 0, "dullness": 0, "oiliness": 0, "dryness": 0,
        "sensitivity": 0, "pigmentation": 0, "dark_circles": 0,
        "comedones": 0, "aging": 0, "dehydration": 0, "barrier_damage_acne": 0,
    }
    state_names = [s["state"] for s in skin_states]

    # Skin type auto-boost
    if skin_type == "Oily":
        scores["oiliness"] += 2
        scores["acne"] += 1
        scores["comedones"] += 1
    elif skin_type == "Dry":
        scores["dryness"] += 2
    elif skin_type == "Combination":
        scores["oiliness"] += 1
        scores["dryness"] += 1

    # Skin state auto-boost
    if "Dehydrated" in state_names:
        scores["dehydration"] += 3
        scores["dullness"] += 1
    if "Sensitized" in state_names or "Compromised Barrier" in state_names:
        scores["sensitivity"] += 3
    if "Congested" in state_names:
        scores["comedones"] += 2
        scores["acne"] += 1

    # User-selected concerns
    # Filter out "none" — it means explicitly no concerns, treat same as empty selection
    selected = [c for c in _get_list(data, "concerns") if c != "none"]
    concern_map = {
        "acne": "acne", "pigmentation": "pigmentation", "dullness": "dullness",
        "dryness": "dryness", "excess_oil": "oiliness", "sensitivity": "sensitivity",
        "dark_circles": "dark_circles", "comedones": "comedones", "aging": "aging",
    }
    for c in selected:
        mapped = concern_map.get(c)
        if mapped:
            scores[mapped] += SIGNAL_WEIGHTS["user_select"]

    # Behavioral signals
    breakouts = data.get("breakouts", "")
    if breakouts == "sometimes":
        scores["acne"] += 1
    elif breakouts == "often":
        scores["acne"] += 2
    elif breakouts == "very_frequent":
        scores["acne"] += 3

    pores = data.get("pores", "")
    if pores in ["visible", "very_visible"]:
        scores["comedones"] += 1
        scores["acne"] += 1

    reaction = data.get("reaction", "")
    if reaction == "burning":
        scores["sensitivity"] += SIGNAL_WEIGHTS["reaction"]
    elif reaction == "redness":
        scores["sensitivity"] += 2
    elif reaction == "slight":
        scores["sensitivity"] += 1

    sleep = data.get("sleep", "")
    if sleep == "<5":
        scores["dullness"] += 2
        scores["dark_circles"] += 1
    elif sleep == "5-6":
        scores["dullness"] += 1
        scores["dark_circles"] += 1

    flaky = data.get("flaky", "")
    if flaky == "yes_often":
        scores["dryness"] += SIGNAL_WEIGHTS["flaky"]
    elif flaky == "sometimes":
        scores["dryness"] += 1

    sun = data.get("sun_exposure", "")
    if sun == "high_sun":
        scores["pigmentation"] += 2
        scores["dullness"] += 1
    elif sun == "medium_sun":
        scores["pigmentation"] += 1

    # Plain text boost
    for concern, count in plain_text_signals.items():
        if concern in scores:
            scores[concern] += min(count, 2) * SIGNAL_WEIGHTS["plain_text"]

    # Age-gated
    if age_group == "adult_28_35":
        scores["aging"] += SIGNAL_WEIGHTS["age_signal"]
        scores["pigmentation"] += 1
    elif age_group == "adult_35_plus":
        scores["aging"] += SIGNAL_WEIGHTS["age_signal"] + 2
        scores["pigmentation"] += 2
        scores["dullness"] += 1

    # Barrier damage acne: acne without oil
    if scores["acne"] >= 2 and oil_score <= 1 and dry_score >= 2:
        scores["barrier_damage_acne"] += 3
        scores["acne"] = max(0, scores["acne"] - 2)

    return scores


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 5 — CONCERN VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════
def validate_concerns(data, scores, skin_type, oil_score, dry_score):
    notes = []
    adjusted = dict(scores)
    selected = [c for c in _get_list(data, "concerns") if c != "none"]
    reaction = data.get("reaction", "")

    # Dryness selected but oily signals are strong — dehydration, not true dryness
    if "dryness" in selected and oil_score >= 4 and dry_score <= 1:
        adjusted["dryness"] = max(0, adjusted["dryness"] - 2)
        notes.append("You selected dry patches — your skin's oily behavior suggests this is dehydration rather than true dryness. Niacinamide in your routine strengthens the skin barrier and addresses both conditions. Glycerin provides gentle hydration safe for oily skin.")

    if "acne" in selected and data.get("breakouts") in ["rare", "sometimes"] and oil_score <= 1:
        adjusted["acne"] = max(0, adjusted["acne"] - 1)
        notes.append("Acne was selected but behavioral signals show minimal breakout frequency and low oil. Priority slightly reduced.")

    if "excess_oil" in selected and skin_type == "Dry":
        adjusted["oiliness"] = max(0, adjusted["oiliness"] - 2)
        notes.append("You selected oily skin but answers indicate dry skin. The shine may be from a damaged barrier rather than true oil production.")

    # Bug 2c — excess_oil selected but will be deferred by sensitivity routing
    # Flag this so the user knows it is coming in Phase 2, not ignored
    if "excess_oil" in selected and reaction in ["burning", "redness"]:
        notes.append("You selected excess oil — your skin's current reactivity means oil-control actives could cause a flare right now. Niacinamide (introduced in Phase 2) regulates sebum while being gentle enough for reactive skin. You will see oil improvement from week 6-8.")

    return adjusted, notes


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 6 — TOP CONCERNS
# ═══════════════════════════════════════════════════════════════════════════════
def get_top_concerns(scores):
    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    filtered = [item for item in sorted_items if item[1] >= 2]
    return [item[0] for item in filtered[:3]]


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 7 — CONFLICT DETECTION
# ═══════════════════════════════════════════════════════════════════════════════
def detect_conflict(top_concerns):
    for pair in CONFLICT_PAIRS:
        if pair[0] in top_concerns and pair[1] in top_concerns:
            return True, pair
    return False, None


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 8 — DULLNESS CAUSE ATTRIBUTION
# ═══════════════════════════════════════════════════════════════════════════════
def attribute_dullness_cause(data, scores, skin_states):
    if scores.get("dullness", 0) < 2:
        return []
    sleep = data.get("sleep", "")
    sun = data.get("sun_exposure", "medium_sun")
    states = [s["state"] for s in skin_states]
    causes = []

    if sleep in ["<5", "5-6"]:
        causes.append({"cause": "sleep_deprivation", "label": "Sleep-related", "ingredients": ["niacinamide", "glycerin"]})
    if sun in ["medium_sun", "high_sun"] and scores.get("pigmentation", 0) >= 1:
        causes.append({"cause": "sun_damage", "label": "Sun damage", "ingredients": ["vitamin_c", "tranexamic_acid"]})
    if "Dehydrated" in states:
        causes.append({"cause": "dehydration", "label": "Dehydration", "ingredients": ["hyaluronic_acid", "glycerin"]})

    if sleep in ["7-8", "6-7"] and scores.get("dullness", 0) >= 3:
        causes = [c for c in causes if c["cause"] != "sleep_deprivation"]
        if not any(c["cause"] == "dehydration" for c in causes):
            causes.append({"cause": "dehydration", "label": "Possible dehydration (not sleep)", "ingredients": ["hyaluronic_acid", "glycerin"]})
    return causes


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 9 — RECOMMENDATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
def get_recommendation(data, skin_type, skin_states, top_concerns, conflict_detected, dullness_causes, age_group):
    experience = data.get("experience", "basic")
    is_beginner = experience in ["none", "basic"]
    has_sensitivity = "sensitivity" in top_concerns
    has_dryness = "dryness" in top_concerns
    has_dehydration = any(s["state"] == "Dehydrated" for s in skin_states)
    has_barrier_dmg = "barrier_damage_acne" in top_concerns

    if conflict_detected:
        return _build_phased_routine(top_concerns, has_sensitivity, has_dryness, has_dehydration)
    return _build_standard_routine(
        data, skin_type, skin_states, top_concerns, is_beginner,
        has_sensitivity, has_dehydration, has_barrier_dmg, dullness_causes, age_group,
    )


def _build_phased_routine(top_concerns, has_sensitivity, has_dryness, has_dehydration):
    ha_or_panthenol = "Hyaluronic Acid serum — apply to damp skin, dehydration is your first priority" if has_dehydration else "Panthenol (B5) serum — barrier repair focus"

    # Bug 2b/5: caffeine is sensitivity_safe=True — add to Phase 1 morning if dark_circles concern
    # There is no medical reason to exclude it from any phase, even barrier repair
    caffeine_step = (
        [{"step": 99, "type": "Eye Cream", "instruction": "Caffeine eye cream — apply cold, morning only. Safe during all phases.", "why": "Sensitivity-safe; no conflict with barrier repair ingredients"}]
        if "dark_circles" in top_concerns else []
    )

    def inject_caffeine(steps):
        """Insert caffeine step before SPF in morning routine if needed."""
        if not caffeine_step:
            return steps
        # find SPF position and insert before it
        spf_idx = next((i for i, s in enumerate(steps) if s["type"] == "SPF"), len(steps))
        return steps[:spf_idx] + caffeine_step + steps[spf_idx:]

    phase1_morning_base = [
        {"step": 1, "type": "Cleanser",    "instruction": "Fragrance-free gentle milk cleanser", "why": "No actives, no SLS, no fragrance"},
        {"step": 2, "type": "Serum",       "instruction": ha_or_panthenol, "why": "Core barrier/hydration repair"},
        {"step": 3, "type": "Moisturizer", "instruction": "Ceramide-rich moisturizer", "why": "Rebuild lipid barrier"},
        {"step": 4, "type": "SPF",         "instruction": "SPF 30-50 — every morning", "why": "Prevents further damage"},
    ]
    phase2_morning_base = [
        {"step": 1, "type": "Cleanser",    "instruction": "Gentle fragrance-free cleanser", "why": "Still fragrance-free"},
        {"step": 2, "type": "Serum",       "instruction": "Niacinamide 5%", "why": "Multi-target: oil control, acne, pigmentation, barrier, and dullness"},
        {"step": 3, "type": "Moisturizer", "instruction": "Light ceramide moisturizer", "why": "Lock in active"},
        {"step": 4, "type": "SPF",         "instruction": "SPF 30-50", "why": "Mandatory"},
    ]
    phase3_morning_base = [
        {"step": 1, "type": "Cleanser",    "instruction": "Gentle cleanser", "why": ""},
        {"step": 2, "type": "Serum",       "instruction": "Niacinamide 5%", "why": "Maintain previous gains"},
        {"step": 3, "type": "Moisturizer", "instruction": "Light moisturizer", "why": ""},
        {"step": 4, "type": "SPF",         "instruction": "SPF 30-50", "why": ""},
    ]

    # Build deferred concern notes — shown in phased routine notes section
    deferred_notes = []
    if "excess_oil" in top_concerns:
        deferred_notes.append("You selected excess oil — Niacinamide in Phase 2 regulates sebum while being gentle enough for your reactive skin. Oil improvement expected from week 6-8.")
    if "dark_circles" in top_concerns:
        deferred_notes.append("Dark circles: Caffeine eye cream is included from Phase 1 — it is safe at all stages. For deeper treatment, a brighter eye serum is added after Phase 3.")
    if "oiliness" in top_concerns:
        deferred_notes.append("Oiliness is addressed by Niacinamide in Phase 2 — sebum regulation improves alongside barrier repair.")

    # Bug 6b framing note — none selected but phased routine triggered by reaction=burning
    none_note = []
    if "none" in top_concerns or not any(c in top_concerns for c in ["acne", "pigmentation", "dullness", "dryness", "sensitivity", "oiliness", "dark_circles", "comedones", "aging"]):
        none_note = ["You indicated no specific concerns — however, your skin's reactivity required a phased approach for medical reasons. Azelaic Acid in Phase 3 is included for skin stability, not because of a concern you selected."]

    phases = [
        {
            "number": 1, "label": "Phase 1 - Barrier Repair", "duration": "Weeks 1-6",
            "focus": "Stabilize your skin barrier before introducing any actives. No exceptions.",
            "morning": inject_caffeine(phase1_morning_base),
            "night": [
                {"step": 1, "type": "Cleanser",    "instruction": "Same gentle milk cleanser", "why": "Consistency"},
                {"step": 2, "type": "Serum",       "instruction": "Centella Asiatica serum", "why": "Anti-inflammatory barrier repair"},
                {"step": 3, "type": "Serum",       "instruction": "Panthenol (B5) serum", "why": "Deep hydration overnight"},
                {"step": 4, "type": "Moisturizer", "instruction": "Ceramide moisturizer — richer at night", "why": "Night repair mode"},
            ],
            "hero_ingredients": ["Ceramides", "Centella Asiatica", "Panthenol", "Hyaluronic Acid"],
        },
        {
            "number": 2, "label": "Phase 2 - First Active", "duration": "Weeks 6-12",
            "focus": "Introduce Niacinamide — addresses acne, pigmentation, oiliness, dullness and barrier simultaneously.",
            "morning": inject_caffeine(phase2_morning_base),
            "night": [
                {"step": 1, "type": "Cleanser",    "instruction": "Gentle cleanser", "why": ""},
                {"step": 2, "type": "Serum",       "instruction": "Niacinamide 5%", "why": "Evening application"},
                {"step": 3, "type": "Moisturizer", "instruction": "Ceramide moisturizer", "why": ""},
            ],
            "hero_ingredients": ["Niacinamide 5%"],
        },
        {
            "number": 3, "label": "Phase 3 - Target Remaining Concerns", "duration": "Weeks 12+",
            "focus": "Add Azelaic Acid — treats acne and pigmentation without aggravating any conflict.",
            "morning": inject_caffeine(phase3_morning_base),
            "night": [
                {"step": 1, "type": "Cleanser",    "instruction": "Gentle cleanser", "why": ""},
                {"step": 2, "type": "Serum",       "instruction": "Azelaic Acid 10%", "why": "Treats acne + pigmentation, safe for dry/sensitive"},
                {"step": 3, "type": "Moisturizer", "instruction": "Ceramide moisturizer", "why": ""},
            ],
            "hero_ingredients": ["Niacinamide 5%", "Azelaic Acid 10%"],
        },
    ]

    base_notes = [
        "Your skin has conflicting concerns — rushing actives will make things worse.",
        "Niacinamide and Azelaic Acid are your hero ingredients — they treat multiple concerns at the intersection.",
        "Do not skip phases. Stability first, treatment second.",
    ]

    return {
        "mode": "phased", "phases": phases, "current_phase": 1,
        "avoid": _build_avoid_list(top_concerns),
        "notes": base_notes + deferred_notes + none_note,
        "ingredients_used": [],
    }


def _build_standard_routine(
    data, skin_type, skin_states, top_concerns, is_beginner,
    has_sensitivity, has_dehydration, has_barrier_dmg, dullness_causes, age_group,
):
    state_names = [s["state"] for s in skin_states]

    # Cleanser
    if has_sensitivity or "Compromised Barrier" in state_names:
        cleanser = "Fragrance-free gentle milk cleanser — no actives, no foaming agents"
    elif skin_type == "Oily" and not has_dehydration:
        cleanser = "Gel cleanser with Salicylic Acid 0.5-1% — controls oil and clears pores"
    elif skin_type == "Oily" and has_dehydration:
        cleanser = "Gentle gel cleanser (no SLS, no actives) — avoid stripping, skin is dehydrated despite oiliness"
    elif skin_type == "Dry":
        cleanser = "Cream or milk cleanser — no SLS, no foaming agents"
    else:
        cleanser = "Gentle balanced pH gel cleanser"

    # Moisturizer
    if skin_type == "Dry" or has_sensitivity:
        moist_am = "Ceramide-rich moisturizer (medium weight)"
        moist_pm = "Ceramide-rich moisturizer (richer at night)"
    elif has_dehydration:
        moist_am = "Water-based gel moisturizer with Glycerin"
        moist_pm = "Slightly richer water-gel moisturizer with Ceramides"
    elif skin_type == "Oily":
        moist_am = "Oil-free gel moisturizer — never skip, dehydrated skin produces more oil"
        moist_pm = "Lightweight water-gel moisturizer"
    else:
        moist_am = "Light moisturizer"
        moist_pm = "Slightly richer moisturizer at night"

    morning_s = []
    night_s = []
    used = []

    # Flags used throughout the routine builder
    reaction = data.get("reaction", "")
    reaction_safe = reaction not in ["burning", "redness"]   # Bug 1a gate — covers SA + Retinol
    none_selected = "none" in _get_list(data, "concerns")    # Bug 6a gate — prevention mode
    selected_raw = [c for c in _get_list(data, "concerns") if c != "none"]

    # Dehydration — always first
    if has_dehydration:
        _add(morning_s, "Hyaluronic Acid serum — apply to damp skin, hydration foundation", "hyaluronic_acid")
        _add(night_s,   "Hyaluronic Acid serum — damp skin before moisturizer", "hyaluronic_acid")
        used.append("hyaluronic_acid")

    # Bug 2a — oily skin user selected dryness: always add Glycerin as safe hydration bridge
    # The concern was downweighted in validate_concerns (medically correct) but
    # the ingredient must appear so the user sees their concern was heard.
    if "dryness" in selected_raw and skin_type == "Oily" and "hyaluronic_acid" not in used:
        _add(morning_s, "Glycerin serum or toner — lightweight hydration safe for oily skin", "glycerin")
        _add(night_s,   "Glycerin — locks in moisture without heaviness", "glycerin")
        used.append("glycerin")

    if has_sensitivity or has_barrier_dmg:
        _add(morning_s, "Centella Asiatica serum — calms and strengthens barrier", "centella")
        _add(night_s,   "Panthenol (B5) serum — deep barrier repair overnight", "panthenol")
        used += ["centella", "panthenol"]
    else:
        if "acne" in top_concerns:
            _add(night_s, "Niacinamide 5% serum — oil control, anti-inflammatory, and brightening", "niacinamide")
            used.append("niacinamide")
            if not is_beginner and reaction_safe and not none_selected:
                # Bug 1a: blocked when reaction=redness or burning
                # Bug 6a: blocked when none selected (prevention mode only)
                sa_strength = "0.5-1%" if data.get("experience") == "intermediate" else "1-2%"
                _add(night_s, f"Salicylic Acid {sa_strength} toner — pore clearing, alternate nights if sensitive", "salicylic_acid")
                used.append("salicylic_acid")
        if has_barrier_dmg:
            _add(night_s, "Azelaic Acid 10% — barrier-driven acne without harsh actives", "azelaic_acid")
            used.append("azelaic_acid")
        if "oiliness" in top_concerns and "acne" not in top_concerns:
            _add(morning_s, "Zinc PCA serum — regulates sebum without drying", "zinc_pca")
            used.append("zinc_pca")
        if "dullness" in top_concerns:
            dc = dullness_causes[0]["cause"] if dullness_causes else "general"
            vitamin_c_safe = reaction_safe  # Bug 1a: same gate covers Vitamin C
            if dc == "sun_damage" and not is_beginner and vitamin_c_safe:
                _add(morning_s, "Vitamin C 10% serum — antioxidant brightening (morning + SPF always)", "vitamin_c")
                used.append("vitamin_c")
            elif "niacinamide" not in used:
                _add(morning_s, "Niacinamide 5% — brightening, sebum regulation, and barrier support", "niacinamide")
                used.append("niacinamide")
        if "pigmentation" in top_concerns:
            if not is_beginner:
                _add(morning_s, "Tranexamic Acid 3-5% — melanin inhibition (highly effective for BD skin tones)", "tranexamic_acid")
                used.append("tranexamic_acid")
            else:
                _add(night_s, "Alpha Arbutin 2% — gentle dark spot reduction for beginners", "alpha_arbutin")
                used.append("alpha_arbutin")
        if "aging" in top_concerns and age_group in ["adult_28_35", "adult_35_plus"]:
            if is_beginner:
                _add(night_s, "Peptide serum — gentle collagen support", "peptides")
                used.append("peptides")
            elif reaction_safe and not none_selected:
                # Bug 1a: Retinol blocked for reaction=redness (User 303, 316)
                # Bug 6a: Retinol is a treatment active — not for prevention mode
                _add(night_s, "Retinol 0.025% — start 2x/week, increase gradually. Never daytime.", "retinol")
                used.append("retinol")
            else:
                # Reaction=redness or none selected — use Peptides as safe alternative
                _add(night_s, "Peptide serum — collagen support safe for your reactive skin", "peptides")
                used.append("peptides")

    # dark_circles caffeine — runs unconditionally regardless of sensitivity or barrier state
    # Caffeine is sensitivity_safe=True — no medical reason to exclude it from any routine
    if "dark_circles" in top_concerns:
        _add(morning_s, "Caffeine eye cream — apply cold, morning only", "caffeine")
        used.append("caffeine")

    def build_steps(serum_list, cleanser_txt, moist_txt, include_spf):
        steps = [{"step": 1, "type": "Cleanser", "instruction": cleanser_txt, "why": "Removes residue without disrupting barrier"}]
        for i, s in enumerate(serum_list, 2):
            steps.append({"step": i, "type": "Serum", "instruction": s["instruction"], "why": s["why"]})
        n = len(steps) + 1
        steps.append({"step": n, "type": "Moisturizer", "instruction": moist_txt, "why": "Seals in actives and maintains barrier hydration"})
        if include_spf:
            # FIX: specific SPF recommendation for high sun exposure users (BD UV Index 9-11)
            sun = data.get("sun_exposure", "")
            spf_instruction = (
                "SPF 50 PA++++ — mandatory for your sun exposure level. Reapply every 2 hours outdoors."
                if sun == "high_sun"
                else "SPF 30-50 — last step every morning, most important anti-aging and anti-pigmentation product"
            )
            steps.append({"step": n+1, "type": "SPF", "instruction": spf_instruction, "why": "Prevents UV-induced melanin overproduction and collagen breakdown"})
        return steps

    # FIX Bug 4: note when routine is derived from behavioral signals without concern selection
    selected_concerns = [c for c in _get_list(data, "concerns") if c != "none"]
    explicitly_none = "none" in _get_list(data, "concerns")
    behavioral_note = []
    if not selected_concerns and top_concerns:
        if explicitly_none:
            behavioral_note = ["You indicated no specific concerns — this routine focuses on prevention, protection, and maintaining your skin's current health."]
        else:
            behavioral_note = ["These recommendations are based on your behavioral answers and age profile, not your selected concerns — you did not select any concerns on the form."]

    return {
        "mode": "standard",
        "morning": build_steps(morning_s, cleanser, moist_am, True),
        "night":   build_steps(night_s, cleanser, moist_pm, False),
        "avoid":   _build_avoid_list(top_concerns),
        "notes":   behavioral_note,
        "ingredients_used": [
            {"label": INGREDIENT_DB[i]["label"], "why": INGREDIENT_DB[i]["why"], "time": INGREDIENT_DB[i]["time"]}
            for i in used if i in INGREDIENT_DB
        ],
    }


def _add(lst, instruction, ingredient_key):
    db = INGREDIENT_DB.get(ingredient_key, {})
    lst.append({"instruction": instruction, "ingredient": ingredient_key, "why": db.get("why", "")})


def _build_avoid_list(top_concerns):
    avoid = []
    seen = set()
    for concern in top_concerns:
        for item in AVOID_MAP.get(concern, []):
            if item not in seen:
                avoid.append(item)
                seen.add(item)
    return avoid


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 10 — SKIN STORY
# ═══════════════════════════════════════════════════════════════════════════════
def build_skin_story(skin_type, skin_states, top_concerns, oil_score, dry_score, data):
    parts = []
    states = [s["state"] for s in skin_states]

    if skin_type == "Oily" and "Dehydrated" in states:
        parts.append("Your skin produces excess oil throughout the day but shows clear signs of water dehydration underneath — a very common condition called dehydrated oily skin.")
        parts.append("The tightness after washing is NOT dryness — it is your skin lacking water while still overproducing oil. These are two separate systems that need separate treatment.")
    elif skin_type == "Oily":
        parts.append("Your skin consistently produces excess sebum throughout the day. This is a structural characteristic of your skin type, not caused by diet or habits alone.")
    elif skin_type == "Dry":
        parts.append("Your skin produces less natural oil than average and shows signs of moisture barrier weakness. Hydration and barrier repair are your non-negotiable foundation.")
    elif skin_type == "Combination":
        parts.append("Your skin behaves differently across zones — oilier in the T-zone and drier or balanced on the cheeks. This is the most common skin type in Bangladesh's climate.")
    else:
        parts.append("Your skin appears relatively balanced — less common in Bangladesh's humid, high-UV environment.")

    if "Sensitized" in states:
        parts.append("Your barrier appears sensitized — likely from product overload or over-exfoliation rather than genetic sensitivity. This is reversible with a consistent gentle approach.")
    if "Compromised Barrier" in states:
        parts.append("Flaking combined with reactive skin strongly indicates a compromised barrier. This is the root cause of several of your other concerns and must be addressed first.")
    if "Congested" in states:
        parts.append("Your pores show active congestion — sebum is not clearing efficiently, which contributes to both blackheads and breakout risk.")

    primary = top_concerns[0] if top_concerns else None
    if primary == "acne":
        parts.append("Acne is your dominant concern. The routine prioritizes sebum regulation and anti-inflammatory ingredients.")
    elif primary == "barrier_damage_acne":
        parts.append("Your breakouts appear barrier-damage driven rather than sebum-driven — an important distinction. Standard acne treatments would make this worse. Barrier repair comes first.")
    elif primary == "pigmentation":
        parts.append("Pigmentation is your primary concern. Bangladesh's UV Index reaches 9-11 from March-October — daily SPF is as important as any brightening ingredient you apply.")
    elif primary == "dehydration":
        parts.append("Dehydration is your most urgent and fastest-to-fix concern. Most people feel a significant difference within 1-2 weeks of consistent hydration layering.")
    elif primary == "sensitivity":
        parts.append("Your skin's reactivity is the main limiting factor right now. Every recommendation is filtered through this — nothing that your barrier cannot currently handle.")

    sleep = data.get("sleep", "")
    if sleep == "<5":
        parts.append("Sleep deprivation is actively affecting your skin — it reduces collagen repair, increases inflammation, and worsens dark circles. The routine alone cannot fully compensate.")

    return " ".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 11 — CONSISTENCY CHECK
# ═══════════════════════════════════════════════════════════════════════════════
def check_consistency(data, skin_type, scores, skin_states, validation_notes):
    issues = list(validation_notes)
    state_names = [s["state"] for s in skin_states]
    after_wash = data.get("after_wash", "")
    after_hours = data.get("after_hours", "")

    if skin_type == "Dry" and scores.get("oiliness", 0) >= 2:
        issues.append("Some oily signals detected despite dry classification — you may be experiencing barrier-related shine rather than true oil production.")
    if data.get("sleep") in ["7-8"] and scores.get("dullness", 0) >= 3:
        issues.append("You report adequate sleep but dullness is high — the cause is likely dehydration or sun damage, not lifestyle. The routine addresses this directly.")
    if "Dehydrated" in state_names and skin_type == "Oily":
        issues.append("Your tight-after-washing + oily-later pattern is NOT a contradiction — it is dehydrated oily skin. Your routine is adjusted accordingly.")

    # GAP 6 FIX: oily right after washing + dry after hours = contradictory pattern.
    # Explain it to the user rather than silently classifying as Combination.
    if after_wash == "oily" and after_hours == "dry":
        issues.append("Your answers show an unusual pattern — oily right after washing but dry or tight within hours. This may indicate dehydrated combination skin, or the oily sensation immediately after washing may be from your cleanser rather than genuine sebum. Try switching to a gentler cleanser and observe whether the morning oily feeling changes.")

    selected = [c for c in _get_list(data, "concerns") if c != "none"]
    if not selected and sum(scores.values()) >= 6:
        issues.append("You did not select any concerns but behavioral answers point to several. Results are based on your behavioral signals — review carefully.")
    return issues


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 12 — TIMELINE & NEXT GOAL
# ═══════════════════════════════════════════════════════════════════════════════
def get_timeline(top_concerns, conflict_detected):
    if conflict_detected:
        return {"weeks": "12-16", "popup": "Your routine has 3 phases over 12+ weeks. Each phase has a specific purpose — do not rush ahead.", "purge_warning": False}
    if not top_concerns:
        return None
    return CONCERN_TIMELINES.get(top_concerns[0])


def get_next_goal(top_concerns, conflict_detected):
    if conflict_detected:
        return "Complete Phase 1 (barrier repair) fully before thinking ahead. Your only goal for the next 6 weeks is stability."
    if not top_concerns:
        return None
    return NEXT_GOALS.get(top_concerns[0])


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 13 — REASONING TRACE
# ═══════════════════════════════════════════════════════════════════════════════
def _build_reasoning_trace(data, skin_type, skin_states, scores, top_concerns, matched_keywords):
    reasons = []
    after_hours = data.get("after_hours", "")
    after_wash = data.get("after_wash", "")
    pores = data.get("pores", "")
    sleep = data.get("sleep", "")
    reaction = data.get("reaction", "")

    if after_hours == "very_oily":
        reasons.append("Skin is very oily 3 hours after washing — strong oily signal (weight: 3)")
    elif after_hours == "oily_tzone":
        reasons.append("T-zone oiliness detected at 3 hours — combination/dehydrated oily indicator")
    elif after_hours == "dry":
        reasons.append("Skin stays dry hours after washing — dry skin confirmed (weight: 3)")
    if after_wash == "tight" and after_hours in ["very_oily", "oily_tzone"]:
        reasons.append("Tight after wash + oily after hours = dehydrated oily skin pattern detected")
    if pores in ["visible", "very_visible"]:
        reasons.append(f"Pores are {pores.replace('_', ' ')} — sebum activity confirmed, acne/comedone risk elevated")
    if reaction in ["burning", "redness"]:
        reasons.append(f"Skin reaction level: {reaction} — sensitivity flagged as priority concern")
    if sleep == "<5":
        reasons.append("Less than 5 hours sleep — dullness and dark circles scores boosted")
    for state in skin_states:
        reasons.append(f"{state['state']} detected: {state['reason'][:70]}...")
    if matched_keywords:
        kw_summary = ", ".join(set([k["maps_to"] for k in matched_keywords[:5]]))
        reasons.append(f"Plain text analysis found signals for: {kw_summary}")
    for concern in top_concerns:
        reasons.append(f"'{concern}' in top concerns — score: {scores.get(concern, 0)}")
    return reasons


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════
def run_skin_engine(data):
    is_valid, missing, filled_data, confidence_penalty = validate_minimum_data(data)
    if not is_valid:
        return {
            "error": True,
            "missing_fields": missing,
            "message": "Not enough information to generate a result. Please answer at minimum: how your skin feels after washing and after a few hours.",
        }
    data = filled_data

    plain_text = data.get("plain_text_input", "") if hasattr(data, 'get') else ""
    if not isinstance(plain_text, str):
        plain_text = ""
    plain_text_signals, matched_keywords = extract_plain_text_signals(plain_text)

    skin_type, oil_score, dry_score = calculate_skin_type(data)
    skin_states = detect_skin_states(data, oil_score, dry_score)
    age_group = data.get("age_group", "adult_25_35")

    scores = calculate_concerns(data, skin_type, skin_states, oil_score, dry_score, plain_text_signals, age_group)
    scores, validation_notes = validate_concerns(data, scores, skin_type, oil_score, dry_score)
    top_concerns = get_top_concerns(scores)
    conflict_detected, conflict_pair = detect_conflict(top_concerns)
    dullness_causes = attribute_dullness_cause(data, scores, skin_states)

    recommendation = get_recommendation(
        data, skin_type, skin_states, top_concerns, conflict_detected, dullness_causes, age_group,
    )
    skin_story = build_skin_story(skin_type, skin_states, top_concerns, oil_score, dry_score, data)
    timeline = get_timeline(top_concerns, conflict_detected)
    next_goal = get_next_goal(top_concerns, conflict_detected)
    issues = check_consistency(data, skin_type, scores, skin_states, validation_notes)
    reasoning = _build_reasoning_trace(data, skin_type, skin_states, scores, top_concerns, matched_keywords)

    return {
        "error":              False,
        "skin_type":          skin_type,
        "skin_states":        skin_states,
        "skin_story":         skin_story,
        "top_concerns":       top_concerns,
        "scores":             scores,
        "conflict_detected":  conflict_detected,
        "conflict_pair":      conflict_pair,
        "recommendation":     recommendation,
        "dullness_causes":    dullness_causes,
        "timeline":           timeline,
        "next_goal":          next_goal,
        "issues":             issues,
        "reasoning":          reasoning,
        "plain_text_signals": plain_text_signals,
        "matched_keywords":   matched_keywords,
        "confidence_penalty": confidence_penalty,
        "age_group":          age_group,
    }
