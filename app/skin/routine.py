# ═══════════════════════════════════════════════════════════════════════════════
# routine.py — Three-Phase Skincare Plan Builder
#
# Every user gets a three-phase plan.
# No exceptions — even simple cases follow the same structure.
#
# Phase 1: Skin Foundation (stabilize and build basics)
# Phase 2: Concern Treatment (target active issues)
# Phase 3: Goal Pursuit (glow, glass skin, anti-aging etc.)
#
# This file takes the engine output from logic.py and the goals from goals.py
# and assembles them into one complete plan the user can read like a story.
# ═══════════════════════════════════════════════════════════════════════════════


# ───────────────────────────────────────────────────────────────────────────────
# PHASE 1 DURATION TABLE
#
# How long Phase 1 (foundation) lasts depends on skin state.
# Sensitive or compromised skin needs more time before actives can start.
# ───────────────────────────────────────────────────────────────────────────────

PHASE1_DURATION = {
    "default":              "Weeks 1 to 2",
    "has_dry":              "Weeks 1 to 3",
    "has_dehydration":      "Weeks 1 to 2",
    "has_sensitivity":      "Weeks 1 to 6",
    "has_conflict":         "Weeks 1 to 6",
    "has_compromised":      "Weeks 1 to 6",
}


# ───────────────────────────────────────────────────────────────────────────────
# PHASE 1 INTRO TEXT
#
# The opening story paragraph shown before the Phase 1 routine.
# Written in plain language so anyone can understand it.
# ───────────────────────────────────────────────────────────────────────────────

PHASE1_INTRO = {
    "default": (
        "Before any treatment begins, your skin needs a stable foundation. "
        "Phase 1 is simple by design — cleanser, moisturizer, and SPF every single day. "
        "This builds the base your skin needs so that when actives are introduced in Phase 2, "
        "they can actually work instead of irritating a fragile surface."
    ),
    "has_sensitivity": (
        "Your skin is currently reactive. This means it cannot handle any active ingredients yet — "
        "they would cause irritation before they could help. "
        "Phase 1 focuses entirely on calming your skin and repairing its natural barrier. "
        "Once the barrier is stable and your skin stops reacting to gentle products, "
        "Phase 2 begins with the safest possible active first."
    ),
    "has_conflict": (
        "Your skin has concerns that conflict with each other at the ingredient level — "
        "treating them at the same time would make both worse. "
        "Phase 1 is the most important phase for you. "
        "It builds the foundation that makes Phase 2 treatment safe and effective. "
        "Do not rush ahead — the results in Phase 3 will be significantly better "
        "because of the patience you show in Phase 1."
    ),
    "has_dehydration": (
        "Your skin is showing dehydration signals — it lacks water, not just oil. "
        "Phase 1 restores that water content before anything else. "
        "Dehydration is the fastest concern to fix — most people notice a difference within 1 to 2 weeks "
        "of consistent hydration. Once your skin is properly hydrated, Phase 2 treatment becomes more effective."
    ),
}


# ───────────────────────────────────────────────────────────────────────────────
# PHASE 2 INTRO TEXT
#
# The story paragraph shown before the Phase 2 routine.
# References the user's specific concerns.
# ───────────────────────────────────────────────────────────────────────────────

def build_phase2_intro(top_concerns, conflict_detected):
    # Base opening
    opening = (
        "Your skin is stable. Now treatment begins. "
        "Phase 2 introduces active ingredients one at a time — "
        "following medical logic, not all at once. "
    )

    # Add concern-specific sentence
    if not top_concerns:
        concern_text = (
            "Since no major concerns were detected, Phase 2 focuses on maintenance and prevention."
        )
    elif conflict_detected:
        concern_text = (
            "Because your concerns conflict, Phase 2 starts with one bridge ingredient — Niacinamide — "
            "which safely treats acne, pigmentation, barrier, and oiliness simultaneously. "
            "Only after your skin shows it tolerates this does Phase 2 expand further."
        )
    else:
        # Build a readable list of concerns
        concern_label_map = {
            "acne":               "acne and breakouts",
            "oiliness":           "excess oiliness",
            "dryness":            "dryness and barrier weakness",
            "sensitivity":        "skin reactivity",
            "pigmentation":       "dark spots and uneven tone",
            "dullness":           "dull and tired-looking skin",
            "comedones":          "blackheads and clogged pores",
            "dark_circles":       "dark circles",
            "dehydration":        "skin dehydration",
            "aging":              "early aging signs",
            "barrier_damage_acne": "barrier-damage driven breakouts",
        }
        readable = []
        for concern in top_concerns:
            readable.append(concern_label_map.get(concern, concern))

        concern_text = (
            "This phase targets your main concerns: "
            + ", ".join(readable)
            + ". "
            "Each ingredient is chosen for your specific profile — not a generic recommendation."
        )

    return opening + concern_text


# ───────────────────────────────────────────────────────────────────────────────
# PHASE 3 INTRO TEXT
#
# The story paragraph shown before the Phase 3 goal section.
# ───────────────────────────────────────────────────────────────────────────────

def build_phase3_intro(goal_roadmap):
    # If no goals were selected
    if not goal_roadmap:
        return (
            "Phase 3 is where your skin reaches its full potential. "
            "Once your concerns are stable, you can focus on enhancement — "
            "deeper glow, better texture, long-term anti-aging. "
            "When you are ready to define your skin goals, you can add them to your plan."
        )

    # Count how many goals are blocked vs active
    blocked_goals = [g for g in goal_roadmap if g["is_blocked"]]
    active_goals = [g for g in goal_roadmap if not g["is_blocked"]]

    if len(blocked_goals) == len(goal_roadmap):
        # All goals are blocked
        return (
            "Your skin goals are in the plan — they are waiting for the right moment. "
            "Phase 1 and 2 are clearing the path. "
            "Once the active concerns are stable, each goal below becomes the focus. "
            "This is not delay — this is the correct order."
        )
    elif len(active_goals) > 0:
        return (
            "Some of your skin goals can start alongside Phase 2 treatment. "
            "Others will begin once your concerns are fully stable. "
            "Your full goal roadmap is below — each one with a clear timeline."
        )
    else:
        return (
            "Phase 3 is your personal enhancement phase. "
            "Every goal below has a specific plan for how your routine supports it over time."
        )


# ───────────────────────────────────────────────────────────────────────────────
# PHASE 1 ROUTINE BUILDER
#
# Phase 1 routine is always simple.
# The exact ingredients depend on skin type and skin states.
# No actives. No strong serums. Foundation only.
# ───────────────────────────────────────────────────────────────────────────────

def build_phase1_routine(skin_type, skin_states, has_dehydration):

    # Collect state names for easy checking
    state_names = [s["state"] for s in skin_states]

    # ── Pick cleanser ──
    has_sensitivity_state = "Sensitized" in state_names or "Compromised Barrier" in state_names

    if has_sensitivity_state:
        cleanser = {
            "step": 1,
            "type": "Cleanser",
            "instruction": "Fragrance-free gentle milk cleanser — no actives, no SLS, no fragrance",
            "why": "Your barrier is sensitive right now. A harsh cleanser will set back recovery.",
        }
    elif skin_type == "Oily" and not has_dehydration:
        cleanser = {
            "step": 1,
            "type": "Cleanser",
            "instruction": "Gentle gel cleanser — no actives yet, just clean the skin",
            "why": "Removes oil without stripping. Phase 2 will introduce the active cleanser.",
        }
    elif skin_type == "Oily" and has_dehydration:
        cleanser = {
            "step": 1,
            "type": "Cleanser",
            "instruction": "Gentle non-stripping gel cleanser — avoid SLS, avoid actives",
            "why": "Your skin is oily but dehydrated. A stripping cleanser makes both worse.",
        }
    elif skin_type == "Dry":
        cleanser = {
            "step": 1,
            "type": "Cleanser",
            "instruction": "Cream or milk cleanser — no SLS, no foaming agents",
            "why": "Dry skin needs a cleanser that cleans without removing what little moisture it has.",
        }
    else:
        cleanser = {
            "step": 1,
            "type": "Cleanser",
            "instruction": "Gentle balanced gel cleanser",
            "why": "Gentle cleansing keeps the skin ready for what comes in Phase 2.",
        }

    # ── Pick moisturizer ──
    if skin_type == "Dry" or has_sensitivity_state:
        moisturizer_am = {
            "step": 3,
            "type": "Moisturizer",
            "instruction": "Ceramide-rich moisturizer — medium weight",
            "why": "Ceramides rebuild the skin barrier. This is the most important product in Phase 1.",
        }
        moisturizer_pm = {
            "step": 3,
            "type": "Moisturizer",
            "instruction": "Ceramide-rich moisturizer — slightly richer formula at night",
            "why": "Skin repairs itself overnight. A richer ceramide formula supports that process.",
        }
    elif has_dehydration:
        moisturizer_am = {
            "step": 3,
            "type": "Moisturizer",
            "instruction": "Water-based gel moisturizer with Glycerin",
            "why": "Restores water content without adding heaviness to oily skin.",
        }
        moisturizer_pm = {
            "step": 3,
            "type": "Moisturizer",
            "instruction": "Slightly richer water-gel moisturizer with Ceramides at night",
            "why": "Night version adds Ceramides to lock in the hydration restored during the day.",
        }
    elif skin_type == "Oily":
        moisturizer_am = {
            "step": 3,
            "type": "Moisturizer",
            "instruction": "Oil-free gel moisturizer — lightweight but do not skip it",
            "why": "Oily skin still needs moisture. Skipping moisturizer makes oil production worse.",
        }
        moisturizer_pm = {
            "step": 3,
            "type": "Moisturizer",
            "instruction": "Lightweight water-gel moisturizer",
            "why": "Light enough for oily skin but still seals in hydration overnight.",
        }
    else:
        moisturizer_am = {
            "step": 3,
            "type": "Moisturizer",
            "instruction": "Light daily moisturizer",
            "why": "Keeps skin hydrated and ready for Phase 2 actives.",
        }
        moisturizer_pm = {
            "step": 3,
            "type": "Moisturizer",
            "instruction": "Slightly richer moisturizer at night",
            "why": "Night moisturizer supports the skin's natural overnight repair cycle.",
        }

    # ── Add hydration serum if dehydrated ──
    hydration_serum = None
    if has_dehydration:
        hydration_serum = {
            "step": 2,
            "type": "Serum",
            "instruction": "Hyaluronic Acid serum — apply to damp skin right after washing",
            "why": "Pulls water into the skin and holds it. Apply while skin is still slightly damp for best absorption.",
        }

    # ── Add barrier serum if sensitized or compromised ──
    barrier_serum_am = None
    barrier_serum_pm = None
    if has_sensitivity_state:
        barrier_serum_am = {
            "step": 2,
            "type": "Serum",
            "instruction": "Centella Asiatica (Cica) serum — calming and barrier-strengthening",
            "why": "Anti-inflammatory. Reduces redness and repairs the barrier without any irritation risk.",
        }
        barrier_serum_pm = {
            "step": 2,
            "type": "Serum",
            "instruction": "Panthenol (Vitamin B5) serum — deep barrier repair while you sleep",
            "why": "B5 draws moisture in and supports the repair of the skin barrier overnight.",
        }

    # ── SPF — always in morning ──
    spf = {
        "step": 4,
        "type": "SPF",
        "instruction": "SPF 30 to 50 — the last step every single morning",
        "why": "SPF is not optional. UV damage undoes every other step in this routine.",
    }

    # ── Assemble morning and night routines ──
    morning = [cleanser]

    if hydration_serum:
        morning.append(hydration_serum)

    if barrier_serum_am:
        morning.append(barrier_serum_am)

    morning.append(moisturizer_am)
    morning.append(spf)

    # Fix step numbers after assembly
    for i, step in enumerate(morning):
        step["step"] = i + 1

    night = [cleanser]

    if hydration_serum:
        night.append(hydration_serum)

    if barrier_serum_pm:
        night.append(barrier_serum_pm)
    elif barrier_serum_am:
        # If only AM serum exists, still add a PM version
        night.append(barrier_serum_pm or barrier_serum_am)

    night.append(moisturizer_pm)

    # Fix step numbers after assembly
    for i, step in enumerate(night):
        step["step"] = i + 1

    return morning, night


# ───────────────────────────────────────────────────────────────────────────────
# MAIN FUNCTION — BUILD THE FULL THREE PHASE PLAN
#
# Takes all the engine output and goal roadmap.
# Returns a complete three-phase plan dictionary.
# ───────────────────────────────────────────────────────────────────────────────

def build_three_phase_plan(
    skin_type,
    skin_states,
    top_concerns,
    conflict_detected,
    recommendation,
    goal_roadmap,
    has_dehydration,
):
    # ── Figure out which Phase 1 intro to use ──
    state_names = [s["state"] for s in skin_states]

    if conflict_detected:
        phase1_intro_key = "has_conflict"
    elif "Sensitized" in state_names or "Compromised Barrier" in state_names:
        phase1_intro_key = "has_sensitivity"
    elif has_dehydration:
        phase1_intro_key = "has_dehydration"
    else:
        phase1_intro_key = "default"

    # ── Figure out Phase 1 duration ──
    if conflict_detected:
        phase1_duration = PHASE1_DURATION["has_conflict"]
    elif "Sensitized" in state_names or "Compromised Barrier" in state_names:
        phase1_duration = PHASE1_DURATION["has_sensitivity"]
    elif "dryness" in top_concerns:
        phase1_duration = PHASE1_DURATION["has_dry"]
    elif has_dehydration:
        phase1_duration = PHASE1_DURATION["has_dehydration"]
    else:
        phase1_duration = PHASE1_DURATION["default"]

    # ── Build Phase 1 routine ──
    phase1_morning, phase1_night = build_phase1_routine(skin_type, skin_states, has_dehydration)

    # ── Phase 2 — use the recommendation from logic.py ──
    # The recommendation already has the correct morning/night steps for the user.
    # We just need to present them as Phase 2.

    if recommendation["mode"] == "phased":
        # Conflict case — Phase 2 from the phased recommendation is already built
        phase2_morning = recommendation["phases"][1]["morning"]
        phase2_night = recommendation["phases"][1]["night"]
        phase2_duration = "Weeks 6 to 12"
    else:
        # Standard case — the whole recommendation IS Phase 2
        phase2_morning = recommendation["morning"]
        phase2_night = recommendation["night"]
        phase2_duration = "Weeks 3 to 12"  # starts earlier for simple cases

    # ── Phase 3 duration ──
    # Phase 3 has no fixed end — it is ongoing maintenance and goal pursuit
    phase3_duration = "Week 12 onward"

    # ── Assemble the complete plan ──
    plan = {

        "phase1": {
            "number":   1,
            "label":    "Phase 1 — Build Your Skin Foundation",
            "duration": phase1_duration,
            "intro":    PHASE1_INTRO[phase1_intro_key],
            "morning":  phase1_morning,
            "night":    phase1_night,
            "what_to_expect": (
                "Your skin will feel more comfortable and less reactive. "
                "Dryness and tightness reduce. Oiliness may still be present. "
                "Do not add any new products during this phase."
            ),
        },

        "phase2": {
            "number":   2,
            "label":    "Phase 2 — Treat Your Skin Concerns",
            "duration": phase2_duration,
            "intro":    build_phase2_intro(top_concerns, conflict_detected),
            "morning":  phase2_morning,
            "night":    phase2_night,
            "what_to_expect": (
                "Active concerns begin to improve. "
                "Acne reduces. Dark spots start to fade. Oiliness becomes more controlled. "
                "Follow the routine consistently — results take 4 to 8 weeks to show clearly."
            ),
            "sequencing_note": (
                "Introduce actives one at a time. "
                "If you are starting a new active ingredient, use it every other day for the first two weeks. "
                "If your skin tolerates it well, move to daily use. "
                "Never start two new actives in the same week."
            ),
        },

        "phase3": {
            "number":   3,
            "label":    "Phase 3 — Pursue Your Skin Goals",
            "duration": phase3_duration,
            "intro":    build_phase3_intro(goal_roadmap),
            "goal_roadmap": goal_roadmap,
            "what_to_expect": (
                "Your skin is stable and concerns are controlled. "
                "Phase 3 is about enhancement — glow, texture, long-term strength. "
                "This phase has no end date. It is your ongoing skin care practice."
            ),
        },

        # Popup warning — shown prominently on the result page
        "popup_warning": (
            "Follow the phases in order. "
            "Do not use Phase 2 products during Phase 1. "
            "Do not use Phase 3 products until Phase 2 is established. "
            "Using everything at once can trigger reactions, breakouts, or barrier damage. "
            "The sequence exists for a medical reason — trust it."
        ),
    }

    return plan
