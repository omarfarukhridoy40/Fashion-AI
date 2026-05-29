# =============================================================================
# logic.py  —  Skin Analysis Engine
#
# This file does one job: take a user's form answers and produce a
# personalized skincare recommendation.
#
# It runs in 13 steps, called in order by run_skin_engine() at the bottom.
# Every function is documented. Every decision has a comment explaining why.
# =============================================================================

from .db_access import (
    get_ingredient_db,
    get_concern_timelines,
    get_conflict_pairs,
    get_avoid_map,
    get_plain_text_keywords,
    get_next_goals,
)


# =============================================================================
# SECTION 1 — SIGNAL WEIGHTS
#
# Not all questions are equally reliable.
# These numbers control how much weight each answer carries.
# Higher number = stronger signal = more influence on the result.
# =============================================================================

SIGNAL_WEIGHTS = {
    "after_hours": 3,   # How skin behaves 3 hours after washing — strongest signal
    "after_wash":  2,   # How skin feels immediately after washing — medium signal
    "pores":       2,   # Pore visibility — medium signal
    "flaky":       2,   # Dry patches — medium signal (only trusted when oil is low)
    "reaction":    3,   # How skin reacts to new products — strongest signal
    "sleep":       1,   # Hours of sleep — weakest signal, lifestyle only
    "user_select": 3,   # Concern the user explicitly selected — strong signal
    "plain_text":  2,   # Keyword found in the user's written description — medium
    "age_signal":  2,   # Age-based concern boost — medium
}


# =============================================================================
# SECTION 2 — DATA STORES (loaded lazily from database via db_access.py)
#
# These used to be hardcoded Python dictionaries.
# They are now loaded from PostgreSQL via the db_access layer on first use.
# The format returned by each function is identical to the old dictionaries —
# so all engine functions below work without any changes.
#
# IMPORTANT: db_access functions are called INSIDE each function that needs
# them — NOT at module level. This prevents errors during Django startup
# before migrations have run. db_access.py caches results for 1 hour so
# calling these functions multiple times per request is free after the
# first call.
#
# SIGNAL_WEIGHTS stays hardcoded — it is a tuning parameter for developers,
# not content that a non-developer would edit through the admin panel.
# =============================================================================


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def _get_list(data, key):
    """
    Safely get a list of values from form data.

    Django form data uses QueryDict which has a getlist() method for
    multi-select fields (like checkboxes). Plain Python dicts do not.
    This function handles both cases so the engine works in tests too.
    """
    if hasattr(data, "getlist"):
        # Django QueryDict — use getlist to get all selected values
        return data.getlist(key)

    # Plain Python dict (used in unit tests)
    value = data.get(key, [])

    if isinstance(value, list):
        return value

    if value:
        return [value]

    return []


def _add_serum(serum_list, instruction, ingredient_key):
    """
    Add a serum step to the morning or night serum list.

    Looks up the ingredient in the database to get the 'why' text.
    If the ingredient is not found, uses an empty string for why.
    """
    ingredient_db = get_ingredient_db()
    ingredient_data = ingredient_db.get(ingredient_key, {})
    why_text = ingredient_data.get("why", "")

    serum_list.append({
        "instruction": instruction,
        "ingredient":  ingredient_key,
        "why":         why_text,
    })


def _build_avoid_list(top_concerns):
    """
    Build the list of ingredients the user should avoid.

    Goes through each of the user's top concerns and collects
    all the things to avoid from AVOID_MAP.
    Uses a set to make sure nothing appears twice.
    """
    avoid_map = get_avoid_map()
    avoid_items = []
    already_added = set()

    for concern in top_concerns:
        items_for_this_concern = avoid_map.get(concern, [])

        for item in items_for_this_concern:
            if item not in already_added:
                avoid_items.append(item)
                already_added.add(item)

    return avoid_items


# =============================================================================
# STEP 0 — INPUT VALIDATION
#
# Before running anything, check that the minimum required fields exist.
# If optional fields are missing, fill them with safe defaults.
# =============================================================================

def validate_minimum_data(data):
    """
    Check that the two required fields are present.
    Fill in safe defaults for any missing optional fields.

    Returns a tuple of four values:
      is_valid          — True if the required fields are present
      missing_required  — list of required field names that are missing
      filled_data       — the data dictionary with defaults filled in
      confidence_penalty — how many optional fields were missing (used for display)
    """

    required_fields = ["after_wash", "after_hours"]
    recommended_fields = ["pores", "flaky", "reaction", "experience", "sleep", "age_group"]

    # Check which required fields are missing
    missing_required = []
    for field in required_fields:
        if not data.get(field):
            missing_required.append(field)

    # If any required field is missing, stop here
    if missing_required:
        return False, missing_required, None, 0

    # Check which recommended fields are missing
    missing_recommended = []
    for field in recommended_fields:
        if not data.get(field):
            missing_recommended.append(field)

    # Safe defaults for missing recommended fields
    defaults = {
        "pores":        "visible",
        "flaky":        "sometimes",
        "reaction":     "slight",
        "experience":   "basic",
        "sleep":        "6-7",
        "age_group":    "adult_25_35",
        "concerns":     [],
        "sun_exposure": "medium_sun",
    }

    # Make a copy of the data so we do not modify the original
    filled = dict(data)

    for field in missing_recommended:
        if not filled.get(field):
            filled[field] = defaults.get(field, "")

    # Each missing field reduces confidence slightly
    confidence_penalty = len(missing_recommended) * 5

    return True, missing_recommended, filled, confidence_penalty


# =============================================================================
# STEP 1 — PLAIN TEXT EXTRACTION
#
# Scan the user's free-text description for known skin concern keywords.
# =============================================================================

def extract_plain_text_signals(plain_text):
    """
    Look for skin concern keywords in the user's written description.

    Returns:
      detected  — dictionary of {concern: number_of_matches}
      matched   — list of {keyword, maps_to} for the confirmation screen
    """

    if not plain_text:
        return {}, []

    plain_text_keywords = get_plain_text_keywords()
    text_lower = plain_text.lower()
    detected = {}
    matched = []

    for concern, keywords in plain_text_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                # Count how many keywords matched for this concern
                current_count = detected.get(concern, 0)
                detected[concern] = current_count + 1

                matched.append({
                    "keyword":  keyword,
                    "maps_to":  concern,
                })

    return detected, matched


# =============================================================================
# STEP 2 — SKIN STATE DETECTION
#
# Detect overlay conditions — these sit on top of skin type.
# Any skin type can have any state.
# States affect which ingredients are safe and how the routine is built.
# =============================================================================

def detect_skin_states(data, oil_score, dry_score):
    """
    Detect overlay skin states from the user's answers.

    Four states are detected:
      Dehydrated           — skin lacks water (can happen to any skin type)
      Mild Dehydration Tendency — skin loses water after washing but self-regulates
      Sensitized           — skin is reactive (either genetic or acquired)
      Congested            — pores are blocked and not clearing properly
      Compromised Barrier  — the skin's moisture barrier is damaged

    Returns a list of state dictionaries. Each has:
      state    — the state name
      reason   — plain English explanation shown to the user
      priority — 1 = highest (treat first), 2 = medium
    """

    states = []
    after_wash = data.get("after_wash", "")
    after_hours = data.get("after_hours", "")
    reaction = data.get("reaction", "")
    experience = data.get("experience", "")
    pores = data.get("pores", "")
    flaky = data.get("flaky", "")

    # --- DEHYDRATED OILY ---
    if after_wash == "tight" and after_hours in ["very_oily", "oily_tzone"]:
        states.append({
            "state":    "Dehydrated",
            "reason":   "Tight right after washing but oily within hours — classic dehydrated oily skin. Your skin lacks water and overproduces oil to compensate. These are two separate systems.",
            "priority": 1,
        })

    # --- DEHYDRATED DRY ---
    elif after_wash == "tight" and after_hours == "dry" and oil_score == 0:
        states.append({
            "state":    "Dehydrated",
            "reason":   "Persistently tight and dry — water content is low across the board. Humectants come first.",
            "priority": 1,
        })

    # --- MILD DEHYDRATION TENDENCY ---
    elif after_wash == "tight" and after_hours == "normal":
        states.append({
            "state":    "Mild Dehydration Tendency",
            "reason":   "Tight right after washing but normalizes within hours — your skin loses surface water immediately after cleansing but self-regulates. Apply a humectant serum to damp skin within 60 seconds of washing.",
            "priority": 2,
        })

    # --- SENSITIZED (ACQUIRED) ---
    if reaction == "burning" and experience in ["intermediate", "advanced"]:
        states.append({
            "state":    "Sensitized",
            "reason":   "Strong reactions combined with an existing product routine suggests acquired sensitivity — likely from over-exfoliation or product overload. This is reversible.",
            "priority": 1,
        })

    # --- SENSITIZED (BARRIER DAMAGE) ---
    elif reaction == "burning":
        states.append({
            "state":    "Sensitized",
            "reason":   "Burning and stinging indicate a compromised barrier. Barrier repair is the first priority before anything else.",
            "priority": 1,
        })

    # --- CONGESTED ---
    if pores in ["visible", "very_visible"] and after_hours in ["oily_tzone", "very_oily"]:
        states.append({
            "state":    "Congested",
            "reason":   "Visible pores combined with persistent oiliness indicates active congestion — sebum is not clearing efficiently from pores.",
            "priority": 2,
        })

    # --- COMPROMISED BARRIER ---
    if flaky == "yes_often" and reaction in ["redness", "burning", "slight"]:
        states.append({
            "state":    "Compromised Barrier",
            "reason":   "Flaking combined with reactive skin strongly indicates a damaged moisture barrier — the root cause of many secondary concerns.",
            "priority": 1,
        })

    return states


# =============================================================================
# STEP 3 — SKIN TYPE CALCULATION
# =============================================================================

def calculate_skin_type(data):
    """
    Determine skin type from behavioral signals.

    Returns a tuple: (skin_type_string, oil_score, dry_score)
    The oil and dry scores are passed to later functions for concern scoring.
    """

    oil = 0
    dry = 0

    after_wash = data.get("after_wash", "")
    after_hours = data.get("after_hours", "")
    pores = data.get("pores", "")
    flaky = data.get("flaky", "")

    # --- AFTER WASH signal ---
    if after_wash == "tight":
        dry += SIGNAL_WEIGHTS["after_wash"]
    elif after_wash == "oily":
        oil += SIGNAL_WEIGHTS["after_wash"]

    # --- AFTER HOURS signal ---
    if after_hours == "dry":
        dry += SIGNAL_WEIGHTS["after_hours"]
    elif after_hours == "oily_tzone":
        oil += 2
        dry += 1
    elif after_hours == "very_oily":
        oil += SIGNAL_WEIGHTS["after_hours"]
    elif after_hours == "normal":
        pass

    # --- PORES signal ---
    if pores == "very_visible":
        oil += SIGNAL_WEIGHTS["pores"]
    elif pores == "visible":
        oil += 1

    # --- FLAKY signal ---
    if flaky != "seasonal" and oil < 3:
        if flaky == "yes_often":
            dry += SIGNAL_WEIGHTS["flaky"]
        elif flaky == "sometimes":
            dry += 1

    # --- SPECIAL CASE OVERRIDES ---

    # OVERRIDE 1: Dehydrated Oily
    if after_wash == "tight" and after_hours in ["very_oily", "oily_tzone"]:
        return "Oily", oil, dry

    # OVERRIDE 2: Normal after hours — apply balance floor
    if after_hours == "normal":
        oil = max(oil, 2)
        dry = max(dry, 2)

    # OVERRIDE 3: T-zone oily + non-tight wash = always Combination
    if after_hours == "oily_tzone" and after_wash in ["normal", "oily"]:
        return "Combination", oil, dry

    # OVERRIDE 4: Dominant dry with high pore visibility
    if after_hours == "dry" and after_wash in ["tight", "normal"] and dry >= 5:
        return "Dry", oil, dry

    # --- MAIN CLASSIFICATION RULES ---
    if oil >= 5 and dry <= 2:
        skin_type = "Oily"
    elif oil >= 4 and dry <= 1:
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


# =============================================================================
# STEP 4 — CONCERN SCORING
# =============================================================================

def calculate_concerns(data, skin_type, skin_states, oil_score, dry_score, plain_text_signals, age_group):
    """
    Build a score for every possible concern.
    """

    scores = {
        "acne":               0,
        "dullness":           0,
        "oiliness":           0,
        "dryness":            0,
        "sensitivity":        0,
        "pigmentation":       0,
        "dark_circles":       0,
        "comedones":          0,
        "aging":              0,
        "dehydration":        0,
        "barrier_damage_acne": 0,
    }

    state_names = [state["state"] for state in skin_states]

    # --- SOURCE 1: Skin type auto-boost ---
    if skin_type == "Oily":
        scores["oiliness"] += 2
        scores["acne"] += 1
        scores["comedones"] += 1
    elif skin_type == "Dry":
        scores["dryness"] += 2
    elif skin_type == "Combination":
        scores["oiliness"] += 1
        scores["dryness"] += 1

    # --- SOURCE 2: Skin state auto-boost ---
    if "Dehydrated" in state_names:
        scores["dehydration"] += 3
        scores["dullness"] += 1
    if "Sensitized" in state_names or "Compromised Barrier" in state_names:
        scores["sensitivity"] += 3
    if "Congested" in state_names:
        scores["comedones"] += 2
        scores["acne"] += 1

    # --- SOURCE 3: User-selected concerns ---
    selected_concerns = [c for c in _get_list(data, "concerns") if c != "none"]

    concern_map = {
        "acne":        "acne",
        "pigmentation": "pigmentation",
        "dullness":    "dullness",
        "dryness":     "dryness",
        "excess_oil":  "oiliness",
        "sensitivity": "sensitivity",
        "dark_circles": "dark_circles",
        "comedones":   "comedones",
        "aging":       "aging",
    }

    for concern_value in selected_concerns:
        internal_key = concern_map.get(concern_value)
        if internal_key:
            scores[internal_key] += SIGNAL_WEIGHTS["user_select"]

    # --- SOURCE 4: Behavioral signals ---
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

    # --- SOURCE 5: Plain text keyword signals ---
    for concern_key, match_count in plain_text_signals.items():
        if concern_key in scores:
            capped_count = min(match_count, 2)
            scores[concern_key] += capped_count * SIGNAL_WEIGHTS["plain_text"]

    # --- SOURCE 6: Age-gated boosts ---
    if age_group == "adult_28_35":
        scores["aging"] += SIGNAL_WEIGHTS["age_signal"]
        scores["pigmentation"] += 1
    elif age_group == "adult_35_plus":
        scores["aging"] += SIGNAL_WEIGHTS["age_signal"] + 2
        scores["pigmentation"] += 2
        scores["dullness"] += 1

    # --- SOURCE 7: Barrier damage acne detection ---
    if scores["acne"] >= 2 and oil_score <= 1 and dry_score >= 2:
        scores["barrier_damage_acne"] += 3
        scores["acne"] = max(0, scores["acne"] - 2)

    return scores


# =============================================================================
# STEP 5 — CONCERN VALIDATION
# =============================================================================

def validate_concerns(data, scores, skin_type, oil_score, dry_score):
    """
    Cross-check user-selected concerns against behavioral evidence.
    """

    notes = []
    adjusted = dict(scores)
    selected = [c for c in _get_list(data, "concerns") if c != "none"]
    reaction = data.get("reaction", "")
    age_group = data.get("age_group", "")

    # Server-side age gate for aging concern
    if age_group in ["teen", "adult_20_27"]:
        selected = [c for c in selected if c != "aging"]
        adjusted["aging"] = 0

    dryness_selected_with_oily_skin = (
        "dryness" in selected and
        oil_score >= 4 and
        dry_score <= 1
    )
    if dryness_selected_with_oily_skin:
        adjusted["dryness"] = max(0, adjusted["dryness"] - 2)
        notes.append("You selected dry patches — your skin's oily behavior suggests this is dehydration rather than true dryness. Niacinamide in your routine strengthens the skin barrier and addresses both conditions. Glycerin provides gentle hydration safe for oily skin.")

    acne_selected_without_strong_signals = (
        "acne" in selected and
        oil_score <= 1
    )
    if acne_selected_without_strong_signals:
        adjusted["acne"] = max(0, adjusted["acne"] - 1)
        notes.append("Acne was selected but behavioral signals show minimal breakout frequency and low oil. Priority slightly reduced.")

    if "excess_oil" in selected and skin_type == "Dry":
        adjusted["oiliness"] = max(0, adjusted["oiliness"] - 2)
        notes.append("You selected oily skin but answers indicate dry skin. The shine may be from a damaged barrier rather than true oil production.")

    if "excess_oil" in selected and reaction in ["burning", "redness"]:
        notes.append("You selected excess oil — your skin's current reactivity means oil-control actives could cause a flare right now. Niacinamide (introduced in Phase 2) regulates sebum while being gentle enough for reactive skin. You will see oil improvement from week 6-8.")

    return adjusted, notes


# =============================================================================
# STEP 6 — TOP CONCERNS
# =============================================================================

def get_top_concerns(scores):
    """
    Return the top 3 concerns with a score of 2 or higher.
    """

    all_sorted = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    above_threshold = [item for item in all_sorted if item[1] >= 2]
    top_3_names = [item[0] for item in above_threshold[: 3]]

    return top_3_names


# =============================================================================
# STEP 7 — CONFLICT DETECTION
# =============================================================================

def detect_conflict(top_concerns):
    """
    Check the top concerns against CONFLICT_PAIRS.
    """

    conflict_pairs = get_conflict_pairs()

    for pair in conflict_pairs:
        concern_a = pair[0]
        concern_b = pair[1]
        both_present = (concern_a in top_concerns) and (concern_b in top_concerns)

        if both_present:
            return True, pair

    return False, None


# =============================================================================
# STEP 8 — DULLNESS CAUSE ATTRIBUTION
# =============================================================================

def attribute_dullness_cause(data, scores, skin_states):
    """
    Figure out WHY the user has dullness.
    """

    if scores.get("dullness", 0) < 2:
        return []

    sleep = data.get("sleep", "")
    sun = data.get("sun_exposure", "medium_sun")
    state_names = [s["state"] for s in skin_states]
    causes = []

    if sleep in ["<5", "5-6"]:
        causes.append({
            "cause":       "sleep_deprivation",
            "label":       "Sleep-related",
            "ingredients": ["niacinamide", "glycerin"],
        })

    if sun in ["medium_sun", "high_sun"] and scores.get("pigmentation", 0) >= 1:
        causes.append({
            "cause":       "sun_damage",
            "label":       "Sun damage",
            "ingredients": ["vitamin_c", "tranexamic_acid"],
        })

    if "Dehydrated" in state_names:
        causes.append({
            "cause":       "dehydration",
            "label":       "Dehydration",
            "ingredients": ["hyaluronic_acid", "glycerin"],
        })

    sleep_is_adequate = sleep in ["7-8", "6-7"]
    dullness_is_high = scores.get("dullness", 0) >= 3

    if sleep_is_adequate and dullness_is_high:
        causes = [c for c in causes if c["cause"] != "sleep_deprivation"]

        dehydration_already_listed = any(c["cause"] == "dehydration" for c in causes)
        if not dehydration_already_listed:
            causes.append({
                "cause":       "dehydration",
                "label":       "Possible dehydration (not sleep)",
                "ingredients": ["hyaluronic_acid", "glycerin"],
            })

    return causes


# =============================================================================
# STEP 9 — RECOMMENDATION ENGINE
# =============================================================================

def get_recommendation(data, skin_type, skin_states, top_concerns, conflict_detected, dullness_causes, age_group):
    """
    Route to the correct routine builder based on whether a conflict exists.
    """

    experience = data.get("experience", "basic")
    is_beginner = experience in ["none", "basic"]
    has_sensitivity = "sensitivity" in top_concerns
    has_barrier_dmg = "barrier_damage_acne" in top_concerns

    has_dehydration = False
    for state in skin_states:
        if state["state"] == "Dehydrated":
            has_dehydration = True

    if conflict_detected:
        return _build_phased_routine(top_concerns, has_sensitivity, has_dehydration)

    return _build_standard_routine(
        data, skin_type, skin_states, top_concerns,
        is_beginner, has_sensitivity, has_dehydration,
        has_barrier_dmg, dullness_causes, age_group
    )


def _build_phased_routine(top_concerns, has_sensitivity, has_dehydration):
    """
    Build a 3-phase treatment routine for users with conflicting concerns.
    """

    if has_dehydration:
        phase1_serum = "Hyaluronic Acid serum — apply to damp skin, dehydration is your first priority"
    else:
        phase1_serum = "Panthenol (B5) serum — barrier repair focus"

    has_dark_circles = "dark_circles" in top_concerns

    def build_morning_steps_with_caffeine(base_steps):
        if not has_dark_circles:
            return base_steps

        spf_position = len(base_steps)
        for i, step in enumerate(base_steps):
            if step["type"] == "SPF":
                spf_position = i
                break

        caffeine_step = {
            "step":        99,
            "type":        "Eye Cream",
            "instruction": "Caffeine eye cream — apply cold, morning only. Safe during all phases.",
            "why":         "Sensitivity-safe; no conflict with barrier repair ingredients",
        }

        new_steps = base_steps[: spf_position] + [caffeine_step] + base_steps[spf_position:]
        return new_steps

    phase1_morning = [
        {"step": 1, "type": "Cleanser",    "instruction": "Fragrance-free gentle milk cleanser",   "why": "No actives, no SLS, no fragrance"},
        {"step": 2, "type": "Serum",       "instruction": phase1_serum,                            "why": "Core barrier or hydration repair"},
        {"step": 3, "type": "Moisturizer", "instruction": "Ceramide-rich moisturizer",             "why": "Rebuild lipid barrier"},
        {"step": 4, "type": "SPF",         "instruction": "SPF 30-50 — every morning",            "why": "Prevents further damage"},
    ]
    phase1_morning = build_morning_steps_with_caffeine(phase1_morning)

    oiliness_or_comedones = any(c in top_concerns for c in ["comedones", "oiliness"])

    if oiliness_or_comedones:
        phase2_focus = "Introduce Niacinamide — regulates sebum, clears pore congestion, addresses comedones and oiliness, and bridges barrier repair."
    else:
        phase2_focus = "Introduce Niacinamide — addresses acne, pigmentation, oiliness, dullness and barrier simultaneously."

    phase2_morning = [
        {"step": 1, "type": "Cleanser",    "instruction": "Gentle fragrance-free cleanser",        "why": "Still fragrance-free"},
        {"step": 2, "type": "Serum",       "instruction": "Niacinamide 5%",                        "why": "Multi-target: oil control, acne, pigmentation, barrier, and dullness"},
        {"step": 3, "type": "Moisturizer", "instruction": "Light ceramide moisturizer",            "why": "Lock in active"},
        {"step": 4, "type": "SPF",         "instruction": "SPF 30-50",                             "why": "Mandatory"},
    ]
    phase2_morning = build_morning_steps_with_caffeine(phase2_morning)

    phase3_morning = [
        {"step": 1, "type": "Cleanser",    "instruction": "Gentle cleanser",      "why": ""},
        {"step": 2, "type": "Serum",       "instruction": "Niacinamide 5%",       "why": "Maintain previous gains"},
        {"step": 3, "type": "Moisturizer", "instruction": "Light moisturizer",    "why": ""},
        {"step": 4, "type": "SPF",         "instruction": "SPF 30-50",            "why": ""},
    ]
    phase3_morning = build_morning_steps_with_caffeine(phase3_morning)

    deferred_notes = []

    if "excess_oil" in top_concerns or "oiliness" in top_concerns:
        deferred_notes.append(
            "You selected excess oil — Niacinamide in Phase 2 directly regulates sebum production "
            "while being gentle enough for your reactive skin. "
            "Sebum improvement is expected from week 6 to 8."
        )

    if has_dark_circles:
        deferred_notes.append(
            "Dark circles: Caffeine eye cream is included from Phase 1 — it is safe at all stages."
        )

    if "comedones" in top_concerns:
        deferred_notes.append(
            "Comedones and oiliness: Niacinamide in Phase 2 directly regulates sebum production "
            "and reduces pore congestion. "
            "Treating comedones without stabilizing oil production first causes them to refill immediately."
        )

    known_concerns = [
        "acne", "pigmentation", "dullness", "dryness", "sensitivity",
        "oiliness", "dark_circles", "comedones", "aging",
    ]
    user_has_no_known_concern = not any(c in top_concerns for c in known_concerns)

    if user_has_no_known_concern:
        deferred_notes.append(
            "You indicated no specific concerns — however, your skin's reactivity required a phased "
            "approach for medical reasons. Azelaic Acid in Phase 3 is included for skin stability, "
            "not because of a concern you selected."
        )

    phases = [
        {
            "number":          1,
            "label":           "Phase 1 - Barrier Repair",
            "duration":        "Weeks 1-6",
            "focus":           "Stabilize your skin barrier before introducing any actives. No exceptions.",
            "morning":         phase1_morning,
            "night": [
                {"step": 1, "type": "Cleanser",    "instruction": "Same gentle milk cleanser",          "why": "Consistency"},
                {"step": 2, "type": "Serum",       "instruction": "Centella Asiatica serum",            "why": "Anti-inflammatory barrier repair"},
                {"step": 3, "type": "Serum",       "instruction": "Panthenol (B5) serum",              "why": "Deep hydration overnight"},
                {"step": 4, "type": "Moisturizer", "instruction": "Ceramide moisturizer — richer at night", "why": "Night repair mode"},
            ],
            "hero_ingredients": ["Ceramides", "Centella Asiatica", "Panthenol", "Hyaluronic Acid"],
        },
        {
            "number":          2,
            "label":           "Phase 2 - First Active",
            "duration":        "Weeks 6-12",
            "focus":           phase2_focus,
            "morning":         phase2_morning,
            "night": [
                {"step": 1, "type": "Cleanser",    "instruction": "Gentle cleanser",          "why": ""},
                {"step": 2, "type": "Serum",       "instruction": "Niacinamide 5%",           "why": "Evening application — sebum regulation, pore clearing, and barrier support"},
                {"step": 3, "type": "Moisturizer", "instruction": "Ceramide moisturizer",    "why": ""},
            ],
            "hero_ingredients": ["Niacinamide 5%"],
        },
        {
            "number":          3,
            "label":           "Phase 3 - Target Remaining Concerns",
            "duration":        "Weeks 12+",
            "focus":           "Add Azelaic Acid — treats acne and pigmentation without aggravating any conflict.",
            "morning":         phase3_morning,
            "night": [
                {"step": 1, "type": "Cleanser",    "instruction": "Gentle cleanser",          "why": ""},
                {"step": 2, "type": "Serum",       "instruction": "Azelaic Acid 10%",         "why": "Treats acne and pigmentation, safe for dry and sensitive skin"},
                {"step": 3, "type": "Moisturizer", "instruction": "Ceramide moisturizer",    "why": ""},
            ],
            "hero_ingredients": ["Niacinamide 5%", "Azelaic Acid 10%"],
        },
    ]

    base_notes = [
        "Your skin has conflicting concerns — rushing actives will make things worse.",
        "Niacinamide and Azelaic Acid are your hero ingredients — they treat multiple concerns at the intersection.",
        "Do not skip phases. Stability first, treatment second.",
    ]

    all_hero_ingredients = []
    for phase in phases:
        for ingredient_name in phase.get("hero_ingredients", []):
            if ingredient_name not in all_hero_ingredients:
                all_hero_ingredients.append(ingredient_name)

    return {
        "mode":             "phased",
        "phases":           phases,
        "current_phase":    1,
        "avoid":            _build_avoid_list(top_concerns),
        "notes":            base_notes + deferred_notes,
        "ingredients_used": all_hero_ingredients,
    }


def _build_standard_routine(data, skin_type, skin_states, top_concerns, is_beginner,
                            has_sensitivity, has_dehydration, has_barrier_dmg,
                            dullness_causes, age_group):
    """
    Build a single morning and night routine for users with no conflicts.
    """

    state_names = [s["state"] for s in skin_states]
    skin_is_sensitive = has_sensitivity or "Compromised Barrier" in state_names

    if skin_is_sensitive:
        cleanser = "Fragrance-free gentle milk cleanser — no actives, no foaming agents"
    elif skin_type == "Oily" and not has_dehydration:
        cleanser = "Gel cleanser with Salicylic Acid 0.5-1% — controls oil and clears pores"
    elif skin_type == "Oily" and has_dehydration:
        cleanser = "Gentle gel cleanser (no SLS, no actives) — avoid stripping, skin is dehydrated despite oiliness"
    elif skin_type == "Dry":
        cleanser = "Cream or milk cleanser — no SLS, no foaming agents"
    else:
        cleanser = "Gentle balanced gel cleanser"

    if skin_type == "Dry" or has_sensitivity:
        moisturizer_morning = "Ceramide-rich moisturizer (medium weight)"
        moisturizer_night = "Ceramide-rich moisturizer (richer at night)"
    elif has_dehydration:
        moisturizer_morning = "Water-based gel moisturizer with Glycerin"
        moisturizer_night = "Slightly richer water-gel moisturizer with Ceramides"
    elif skin_type == "Oily":
        moisturizer_morning = "Oil-free gel moisturizer — never skip, dehydrated skin produces more oil"
        moisturizer_night = "Lightweight water-gel moisturizer"
    else:
        moisturizer_morning = "Light moisturizer"
        moisturizer_night = "Slightly richer moisturizer at night"

    reaction = data.get("reaction", "")
    reaction_safe = reaction not in ["burning", "redness"]
    none_selected = "none" in _get_list(data, "concerns")
    selected_raw = [c for c in _get_list(data, "concerns") if c != "none"]

    morning_serums = []
    night_serums = []
    used_keys = []

    # --- Dehydration — always the first serum if present ---
    if has_dehydration:
        _add_serum(morning_serums, "Hyaluronic Acid serum — apply to damp skin, hydration foundation", "hyaluronic_acid")
        _add_serum(night_serums,   "Hyaluronic Acid serum — damp skin before moisturizer",             "hyaluronic_acid")
        used_keys.append("hyaluronic_acid")

    # --- Glycerin for oily users who selected dryness ---
    oily_user_selected_dryness = (
        "dryness" in selected_raw and
        skin_type == "Oily" and
        "hyaluronic_acid" not in used_keys
    )
    if oily_user_selected_dryness:
        _add_serum(morning_serums, "Glycerin serum or toner — lightweight hydration safe for oily skin", "glycerin")
        _add_serum(night_serums,   "Glycerin — locks in moisture without heaviness",                      "glycerin")
        used_keys.append("glycerin")

    # --- Route based on sensitivity ---
    if has_sensitivity or has_barrier_dmg:
        _add_serum(morning_serums, "Centella Asiatica serum — calms and strengthens barrier", "centella")
        _add_serum(night_serums,   "Panthenol (B5) serum — deep barrier repair overnight",   "panthenol")
        used_keys += ["centella", "panthenol"]

    else:
        # Active treatment route

        # Acne
        if "acne" in top_concerns:
            _add_serum(night_serums, "Niacinamide 5% serum — oil control, anti-inflammatory, and brightening", "niacinamide")
            used_keys.append("niacinamide")
            if not is_beginner and reaction_safe and not none_selected:
                strength = "0.5-1%" if data.get("experience") == "intermediate" else "1-2%"
                _add_serum(night_serums, f"Salicylic Acid {strength} toner — pore clearing, alternate nights if sensitive", "salicylic_acid")
                used_keys.append("salicylic_acid")

        # Barrier damage acne
        if has_barrier_dmg:
            _add_serum(night_serums, "Azelaic Acid 10% — barrier-driven acne without harsh actives", "azelaic_acid")
            used_keys.append("azelaic_acid")

        # Comedones
        if "comedones" in top_concerns and "niacinamide" not in used_keys:
            _add_serum(night_serums, "Niacinamide 5% serum — pore regulation and sebum control (essential for comedones)", "niacinamide")
            used_keys.append("niacinamide")
            if not is_beginner and reaction_safe and not none_selected:
                strength = "0.5-1%" if data.get("experience") == "intermediate" else "1-2%"
                _add_serum(night_serums, f"Salicylic Acid {strength} toner — dissolves sebum plugs in pores", "salicylic_acid")
                used_keys.append("salicylic_acid")

        # Oiliness (only if acne and comedones are not already handling it)
        oiliness_not_already_covered = (
            "oiliness" in top_concerns and
            "acne" not in top_concerns and
            "comedones" not in top_concerns
        )
        if oiliness_not_already_covered:
            _add_serum(morning_serums, "Zinc PCA serum — regulates sebum without drying", "zinc_pca")
            used_keys.append("zinc_pca")

        # Dullness
        if "dullness" in top_concerns:
            primary_cause = dullness_causes[0]["cause"] if dullness_causes else "general"
            vitamin_c_safe = reaction_safe

            if primary_cause == "sun_damage" and not is_beginner and vitamin_c_safe:
                _add_serum(morning_serums, "Vitamin C 10% serum — antioxidant brightening (morning + SPF always)", "vitamin_c")
                used_keys.append("vitamin_c")
            elif "niacinamide" not in used_keys:
                _add_serum(morning_serums, "Niacinamide 5% — brightening, sebum regulation, and barrier support", "niacinamide")
                used_keys.append("niacinamide")

        # Pigmentation
        if "pigmentation" in top_concerns:
            if not is_beginner:
                _add_serum(morning_serums, "Tranexamic Acid 3-5% — melanin inhibition (highly effective for Bangladesh skin tones)", "tranexamic_acid")
                used_keys.append("tranexamic_acid")
            else:
                _add_serum(night_serums, "Alpha Arbutin 2% — gentle dark spot reduction for beginners", "alpha_arbutin")
                used_keys.append("alpha_arbutin")
            if "niacinamide" not in used_keys:
                _add_serum(morning_serums, "Niacinamide 5% — fades pigmentation and regulates sebum simultaneously", "niacinamide")
                used_keys.append("niacinamide")

        # Aging
        user_is_old_enough_for_aging = age_group in ["adult_28_35", "adult_35_plus"]
        if "aging" in top_concerns and user_is_old_enough_for_aging:
            if is_beginner:
                _add_serum(night_serums, "Peptide serum — gentle collagen support", "peptides")
                used_keys.append("peptides")
            elif reaction_safe and not none_selected:
                _add_serum(night_serums, "Retinol 0.025% — start 2x/week, increase gradually. Never daytime.", "retinol")
                used_keys.append("retinol")
            else:
                _add_serum(night_serums, "Peptide serum — collagen support safe for your reactive skin", "peptides")
                used_keys.append("peptides")

    # --- Dark circles — always runs ---
    if "dark_circles" in top_concerns:
        _add_serum(morning_serums, "Caffeine eye cream — apply cold, morning only", "caffeine")
        used_keys.append("caffeine")

    # --- Build the final step-by-step routines ---
    def build_routine_steps(serum_list, cleanser_text, moisturizer_text, include_spf):
        steps = []

        steps.append({
            "step":        1,
            "type":        "Cleanser",
            "instruction": cleanser_text,
            "why":         "Removes residue without disrupting barrier",
        })

        for serum in serum_list:
            next_step_number = len(steps) + 1
            steps.append({
                "step":        next_step_number,
                "type":        "Serum",
                "instruction": serum["instruction"],
                "why":         serum["why"],
            })

        steps.append({
            "step":        len(steps) + 1,
            "type":        "Moisturizer",
            "instruction": moisturizer_text,
            "why":         "Seals in actives and maintains barrier hydration",
        })

        if include_spf:
            sun = data.get("sun_exposure", "")
            if sun == "high_sun":
                spf_instruction = "SPF 50 PA++++ — mandatory for your sun exposure level. Reapply every 2 hours outdoors."
            else:
                spf_instruction = "SPF 30-50 — last step every morning, most important anti-aging and anti-pigmentation product"

            steps.append({
                "step":        len(steps) + 1,
                "type":        "SPF",
                "instruction": spf_instruction,
                "why":         "Prevents UV-induced melanin overproduction and collagen breakdown",
            })

        return steps

    morning_steps = build_routine_steps(morning_serums, cleanser, moisturizer_morning, include_spf=True)
    night_steps = build_routine_steps(night_serums,   cleanser, moisturizer_night,   include_spf=False)

    # --- Build note for when routine is based on behavioral signals only ---
    explicitly_none = "none" in _get_list(data, "concerns")
    selected_by_user = [c for c in _get_list(data, "concerns") if c != "none"]
    routine_notes = []

    if not selected_by_user and top_concerns:
        if explicitly_none:
            routine_notes.append("You indicated no specific concerns — this routine focuses on prevention, protection, and maintaining your skin's current health.")
        else:
            routine_notes.append("These recommendations are based on your behavioral answers and age profile, not your selected concerns.")

    # --- Build ingredient intelligence list ---
    ingredient_db = get_ingredient_db()
    ingredients_used = []
    for key in used_keys:
        if key in ingredient_db:
            ingredient_data = ingredient_db[key]
            ingredients_used.append({
                "label": ingredient_data["label"],
                "why":   ingredient_data["why"],
                "time":  ingredient_data["time"],
            })

    return {
        "mode":             "standard",
        "morning":          morning_steps,
        "night":            night_steps,
        "avoid":            _build_avoid_list(top_concerns),
        "notes":            routine_notes,
        "ingredients_used": ingredients_used,
    }


# =============================================================================
# STEP 10 — SKIN STORY
# =============================================================================

def build_skin_story(skin_type, skin_states, top_concerns, oil_score, dry_score, data):
    """
    Generate a natural language summary of the user's skin.
    """

    sentence_parts = []
    state_names = [s["state"] for s in skin_states]

    if skin_type == "Oily" and "Dehydrated" in state_names:
        sentence_parts.append("Your skin produces excess oil throughout the day but shows clear signs of water dehydration underneath — a very common condition called dehydrated oily skin.")
        sentence_parts.append("The tightness after washing is NOT dryness — it is your skin lacking water while still overproducing oil. These are two separate systems that need separate treatment.")
    elif skin_type == "Oily":
        sentence_parts.append("Your skin consistently produces excess sebum throughout the day. This is a structural characteristic of your skin type, not caused by diet or habits alone.")
    elif skin_type == "Dry":
        sentence_parts.append("Your skin produces less natural oil than average and shows signs of moisture barrier weakness. Hydration and barrier repair are your non-negotiable foundation.")
    elif skin_type == "Combination":
        sentence_parts.append("Your skin behaves differently across zones — oilier in the T-zone and drier or balanced on the cheeks. This is the most common skin type in Bangladesh's climate.")
    else:
        sentence_parts.append("Your skin appears relatively balanced — less common in Bangladesh's humid, high-UV environment.")

    if "Sensitized" in state_names:
        sentence_parts.append("Your barrier appears sensitized — likely from product overload or over-exfoliation rather than genetic sensitivity. This is reversible with a consistent gentle approach.")

    if "Compromised Barrier" in state_names:
        sentence_parts.append("Flaking combined with reactive skin strongly indicates a compromised barrier. This is the root cause of several of your other concerns and must be addressed first.")

    if "Congested" in state_names:
        sentence_parts.append("Your pores show active congestion — sebum is not clearing efficiently, which contributes to both blackheads and breakout risk.")

    primary_concern = top_concerns[0] if top_concerns else None

    if primary_concern == "acne":
        sentence_parts.append("Acne is your dominant concern. The routine prioritizes sebum regulation and anti-inflammatory ingredients.")
    elif primary_concern == "barrier_damage_acne":
        sentence_parts.append("Your breakouts appear barrier-damage driven rather than sebum-driven — an important distinction. Standard acne treatments would make this worse. Barrier repair comes first.")
    elif primary_concern == "pigmentation":
        sentence_parts.append("Pigmentation is your primary concern. Bangladesh's UV Index reaches 9-11 from March-October — daily SPF is as important as any brightening ingredient you apply.")
    elif primary_concern == "dehydration":
        sentence_parts.append("Dehydration is your most urgent and fastest-to-fix concern. Most people feel a significant difference within 1-2 weeks of consistent hydration layering.")
    elif primary_concern == "sensitivity":
        sentence_parts.append("Your skin's reactivity is the main limiting factor right now. Every recommendation is filtered through this — nothing that your barrier cannot currently handle.")

    if data.get("sleep") == "<5":
        sentence_parts.append("Sleep deprivation is actively affecting your skin — it reduces collagen repair, increases inflammation, and worsens dark circles. The routine alone cannot fully compensate.")

    return " ".join(sentence_parts)


# =============================================================================
# STEP 11 — CONSISTENCY CHECK
# =============================================================================

def check_consistency(data, skin_type, scores, skin_states, validation_notes):
    """
    Identify unusual patterns in the data and generate explanatory notes.
    """

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

    if after_wash == "oily" and after_hours == "dry":
        issues.append("Your answers show an unusual pattern — oily right after washing but dry or tight within hours. This may indicate dehydrated combination skin, or the oily sensation right after washing may be from your cleanser rather than genuine sebum. Try switching to a gentler cleanser and observe whether the pattern changes.")

    selected = [c for c in _get_list(data, "concerns") if c != "none"]
    if not selected and sum(scores.values()) >= 6:
        issues.append("You did not select any concerns but behavioral answers point to several. Results are based on your behavioral signals — review carefully.")

    return issues


# =============================================================================
# STEP 12 — TIMELINE AND NEXT GOAL
# =============================================================================

def get_timeline(top_concerns, conflict_detected):
    """
    Return the expected improvement timeline for the primary concern.
    """

    if conflict_detected:
        return {
            "weeks":         "12-16",
            "popup":         "Your routine has 3 phases over 12+ weeks. Each phase has a specific purpose — do not rush ahead.",
            "purge_warning": False,
        }

    if not top_concerns:
        return None

    concern_timelines = get_concern_timelines()
    primary_concern = top_concerns[0]
    return concern_timelines.get(primary_concern)


def get_next_goal(top_concerns, conflict_detected):
    """
    Return the next thing the user should focus on after their first milestone.
    """

    if conflict_detected:
        return "Complete Phase 1 (barrier repair) fully before thinking ahead. Your only goal for the next 6 weeks is stability."

    if not top_concerns:
        return None

    next_goals = get_next_goals()
    primary_concern = top_concerns[0]
    return next_goals.get(primary_concern)


# =============================================================================
# STEP 13 — REASONING TRACE
# =============================================================================

def _build_reasoning_trace(data, skin_type, skin_states, scores, top_concerns, matched_keywords):
    """
    Build a transparency log showing how each conclusion was reached.
    """

    reasons = []
    after_hours = data.get("after_hours", "")
    after_wash = data.get("after_wash", "")
    pores = data.get("pores", "")
    sleep = data.get("sleep", "")
    reaction = data.get("reaction", "")

    if after_hours == "very_oily":
        reasons.append("Skin is very oily 3 hours after washing — strong oily signal (weight: 3)")
    elif after_hours == "oily_tzone":
        reasons.append("T-zone oiliness detected at 3 hours — combination or dehydrated oily indicator")
    elif after_hours == "dry":
        reasons.append("Skin stays dry hours after washing — dry skin confirmed (weight: 3)")

    if after_wash == "tight" and after_hours in ["very_oily", "oily_tzone"]:
        reasons.append("Tight after wash + oily after hours = dehydrated oily skin pattern detected")

    if pores in ["visible", "very_visible"]:
        reasons.append(f"Pores are {pores.replace('_', ' ')} — sebum activity confirmed, acne and comedone risk elevated")

    if reaction in ["burning", "redness"]:
        reasons.append(f"Skin reaction level: {reaction} — sensitivity flagged as priority concern")

    if sleep == "<5":
        reasons.append("Less than 5 hours sleep — dullness and dark circles scores boosted")

    for state in skin_states:
        reasons.append(f"{state['state']} detected: {state['reason'][: 70]}...")

    if matched_keywords:
        unique_concerns = set(k["maps_to"] for k in matched_keywords[: 5])
        reasons.append(f"Plain text analysis found signals for: {', '.join(unique_concerns)}")

    for concern in top_concerns:
        reasons.append(f"'{concern}' in top concerns — score: {scores.get(concern, 0)}")

    return reasons


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def run_skin_engine(data):
    """
    Run the complete skin analysis engine.

    Takes the form data (request.POST from Django) and returns
    a complete result dictionary containing everything the templates need.

    If required fields are missing, returns an error dictionary instead.
    """

    # --- Step 0: Validate input ---
    is_valid, missing, filled_data, confidence_penalty = validate_minimum_data(data)

    if not is_valid:
        return {
            "error":          True,
            "missing_fields": missing,
            "message":        "Not enough information to generate a result. Please answer at minimum: how your skin feels after washing and after a few hours.",
        }

    data = filled_data

    # --- Step 1: Extract plain text signals ---
    plain_text = data.get("plain_text_input", "") if hasattr(data, "get") else ""
    if not isinstance(plain_text, str):
        plain_text = ""
    plain_text_signals, matched_keywords = extract_plain_text_signals(plain_text)

    # --- Step 2: Detect skin type ---
    skin_type, oil_score, dry_score = calculate_skin_type(data)

    # --- Step 3: Detect skin states ---
    skin_states = detect_skin_states(data, oil_score, dry_score)

    # --- Step 4: Get age group ---
    age_group = data.get("age_group", "adult_25_35")

    # --- Step 5: Score all concerns ---
    scores = calculate_concerns(data, skin_type, skin_states, oil_score, dry_score, plain_text_signals, age_group)

    # --- Step 6: Validate concern selections ---
    scores, validation_notes = validate_concerns(data, scores, skin_type, oil_score, dry_score)

    # --- Step 7: Get top 3 concerns ---
    top_concerns = get_top_concerns(scores)

    # --- Step 8: Detect conflicts ---
    conflict_detected, conflict_pair = detect_conflict(top_concerns)

    # --- Step 9: Attribute dullness cause ---
    dullness_causes = attribute_dullness_cause(data, scores, skin_states)

    # --- Step 10: Build recommendation ---
    recommendation = get_recommendation(
        data, skin_type, skin_states, top_concerns,
        conflict_detected, dullness_causes, age_group
    )

    # --- Step 11: Build skin story ---
    skin_story = build_skin_story(skin_type, skin_states, top_concerns, oil_score, dry_score, data)

    # --- Step 12: Get timeline and next goal ---
    timeline = get_timeline(top_concerns, conflict_detected)
    next_goal = get_next_goal(top_concerns, conflict_detected)

    # --- Step 13: Consistency check and reasoning trace ---
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
        "show_confidence_warning": confidence_penalty >= 15,
        "age_group":          age_group,
    }
