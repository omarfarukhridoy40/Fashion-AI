import json

from django.shortcuts import render

from .logic import run_skin_engine
from .masks import get_mask_recommendations
from .goals import build_goal_roadmap, get_goal_choices
from .routine import build_three_phase_plan
from .models import UserSkinProfile


def _run_full_analysis(post_data):
    """
    Run the skin engine and attach the full enrichment every template expects.

    This is the single source of orchestration shared by skin_form (POST) and
    confirm_result (POST). It replaces the identical block that was previously
    duplicated in both views.

    On engine validation failure run_skin_engine returns a dict with
    "error": True (and none of the analysis keys), so we return that dict
    untouched and let the caller re-render the form. On success we enrich the
    result with goal_roadmap, masks, three_phase_plan and selected_goals.
    """
    result = run_skin_engine(post_data)

    # Missing required fields -> the engine returns an error dict that does NOT
    # contain top_concerns / skin_type / etc. The enrichment below reads those
    # keys, so we must bail out before touching them.
    if result.get("error"):
        return result

    # getlist keeps EVERY selected goal, not just the last one (multi-select).
    selected_goals = post_data.getlist("skin_goals")

    goal_roadmap = build_goal_roadmap(
        selected_goals=selected_goals,
        top_concerns=result["top_concerns"],
        conflict_detected=result["conflict_detected"],
    )

    masks = get_mask_recommendations(
        skin_type=result["skin_type"],
        top_concerns=result["top_concerns"],
        skin_states=result["skin_states"],
    )

    # Dehydration drives phase messaging — compute it once from the states list.
    has_dehydration = any(s["state"] == "Dehydrated" for s in result["skin_states"])

    three_phase_plan = build_three_phase_plan(
        skin_type=result["skin_type"],
        skin_states=result["skin_states"],
        top_concerns=result["top_concerns"],
        conflict_detected=result["conflict_detected"],
        recommendation=result["recommendation"],
        goal_roadmap=goal_roadmap,
        has_dehydration=has_dehydration,
    )

    # Attach the enrichment that confirm.html and result.html render.
    result["goal_roadmap"] = goal_roadmap
    result["masks"] = masks
    result["three_phase_plan"] = three_phase_plan
    result["selected_goals"] = selected_goals

    return result


def _persist_skin_profile(request, result):
    """
    Persist a confirmed, successful analysis to UserSkinProfile.

    Called ONLY from confirm_result on the success path — never on the
    confirm.html render path and never when the engine returned an error.

    Field mapping uses the keys verified in skin/logic.py run_skin_engine():
      skin_type          -> result["skin_type"] (str)
      skin_states        -> json.dumps(result["skin_states"]) (list of dicts)
      top_concerns       -> comma-joined result["top_concerns"] (concern keys)
      primary_concern    -> first / highest-priority concern key
      conflict_detected  -> result["conflict_detected"] (the engine has NO
                            "conflicts" key, so we read the real boolean)
      raw_input          -> verbatim questionnaire submission as a dict-of-lists
    """
    # Defensive guard: never write a failed analysis, even if mis-called.
    if result.get("error"):
        return

    # top_concerns is already ordered highest-priority-first by the engine.
    top_concerns = result.get("top_concerns", []) or []
    primary_concern = top_concerns[0] if top_concerns else ""

    # Lossless snapshot of the raw questionnaire submission, kept so a later
    # "View full routine" brief can rebuild a QueryDict from it and re-run the
    # engine to regenerate the full routine on demand (we store INPUT, not output).
    #
    # request.POST.lists() yields (key, [all values]); building a dict-of-lists
    # this way preserves EVERY value of multi-value fields (concerns, skin_goals).
    # We must NOT use request.POST.dict() / dict(request.POST) here: those keep
    # only one value per key and would silently truncate multi-selects — the exact
    # bug fixed in Brief 01. The result is JSON-serialisable (strings and lists of
    # strings). csrfmiddlewaretoken (not data) and confirmed (a control flag, not
    # questionnaire input) are dropped.
    raw_input = {
        key: values
        for key, values in request.POST.lists()
        if key not in ("csrfmiddlewaretoken", "confirmed")
    }

    defaults = {
        "skin_type":         result.get("skin_type", ""),
        # JSON keeps the full {state, reason, priority} dicts for the dashboard.
        "skin_states":       json.dumps(result.get("skin_states", [])),
        # Comma-separated concern keys — a consistent, parseable label list.
        "top_concerns":      ",".join(top_concerns),
        "primary_concern":   primary_concern,
        "conflict_detected": bool(result.get("conflict_detected", False)),
        # Lossless raw input; on re-analysis it is overwritten with the latest
        # submission, which is the correct behaviour.
        "raw_input":         raw_input,
        # routine_start_date is intentionally NOT set here — it is owned by a
        # later "start routine" brief. Omitting it leaves new rows null and
        # preserves any existing value when a returning user re-analyses.
    }

    if request.user.is_authenticated:
        # Authenticated users key on the account so re-analysis updates the same
        # row instead of stacking new ones. Preferring linked_user means we never
        # write a second anonymous row for someone who is logged in.
        UserSkinProfile.objects.update_or_create(
            linked_user=request.user,
            defaults=defaults,
        )
    else:
        # session_key can be None until the session is saved — force a save so we
        # have a stable key to attach the anonymous profile to.
        if not request.session.session_key:
            request.session.save()

        UserSkinProfile.objects.update_or_create(
            linked_user=None,
            session_key=request.session.session_key,
            defaults=defaults,
        )


def skin_form(request):
    """
    Main skin analysis form.

    GET  -> render the empty questionnaire.
    POST -> run the full analysis and ALWAYS show the confirmation screen.
            On engine error, re-render the form with the error message.

    The old "confirmed" branch is gone: confirm_result is now the single path
    that renders result.html and writes to the database.
    """
    goal_choices = get_goal_choices()

    if request.method == "POST":
        result = _run_full_analysis(request.POST)

        # Missing required answers — show the form again with the engine message.
        if result.get("error"):
            return render(request, "skin_profile/skin_form.html", {
                "form_error":   result["message"],
                "goal_choices": goal_choices,
            })

        # Success always goes to the confirmation screen first.
        return render(request, "skin_profile/confirm.html", result)

    return render(request, "skin_profile/skin_form.html", {
        "goal_choices": goal_choices,
    })


def confirm_result(request):
    """
    Confirmation handler — the user clicked "Yes, show my routine".

    Re-runs the full analysis from the re-posted fields, persists the confirmed
    profile, then renders the final result page. This view is the single source
    of truth for both the confirmed render and the DB write.
    """
    if request.method == "POST":
        result = _run_full_analysis(request.POST)

        # If the re-posted data somehow fails validation, fall back to the form.
        if result.get("error"):
            return render(request, "skin_profile/skin_form.html", {
                "form_error":   result["message"],
                "goal_choices": get_goal_choices(),
            })

        # Persist only on the confirmed success path.
        _persist_skin_profile(request, result)

        return render(request, "skin_profile/result.html", result)

    return render(request, "skin_profile/skin_form.html", {
        "goal_choices": get_goal_choices(),
    })