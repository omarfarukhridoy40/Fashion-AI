import json

from django.contrib.auth.decorators import login_required
from django.http import QueryDict
from django.shortcuts import redirect, render
from django.utils import timezone

from .logic import run_skin_engine
from .masks import get_mask_recommendations
from .goals import build_goal_roadmap, get_goal_choices
from .routine import build_three_phase_plan
from .db_access import get_ingredient_db
from .models import Product, UserSkinProfile


# Budget tiers ordered cheapest-first — the BD audience is budget-conscious, so we
# surface the lowest tier first. Anything unexpected sorts last (via .get default).
_BUDGET_ORDER = {"low": 0, "medium": 1, "high": 2}

# Skin states that mark a user as sensitivity-restricted. Mirrors masks.py exactly
# so product filtering and mask filtering use the SAME authoritative signal.
_SENSITIVITY_STATES = {"Sensitized", "Compromised Barrier"}


def _ingredient_keys_from_result(result):
    """
    Best-effort recovery of the ingredient KEY strings the routine recommends.

    The engine does not expose a list of ingredient keys: run_skin_engine() has no
    "ingredients_to_use" key, the rendered morning/night steps drop the per-serum
    "ingredient" key, and recommendation["ingredients_used"] carries display LABELS
    (standard mode: {label, why, time}; phased mode: hero-ingredient label strings),
    not keys. Product.ingredient_key matches Ingredient.key, so we must map to keys.

    We reverse the ingredient DB (key -> {label, ...}) into a label -> key map and
    look each used label up. Labels that don't resolve are skipped — which simply
    means no products for them (never a fabricated match). Order is preserved and
    de-duplicated.
    """
    recommendation = result.get("recommendation") or {}
    used = recommendation.get("ingredients_used") or []

    # Pull the label out of each entry: standard mode entries are dicts with a
    # "label"; phased mode entries are plain label strings.
    used_labels = []
    for entry in used:
        if isinstance(entry, dict):
            label = entry.get("label", "")
        else:
            label = entry
        if label:
            used_labels.append(label)

    # Build a label -> key reversal from the ingredient DB (cached; keyed by key).
    ingredient_db = get_ingredient_db()
    label_to_key = {}
    for key, data in ingredient_db.items():
        label = (data or {}).get("label")
        if label:
            label_to_key.setdefault(label, key)

    keys = []
    seen = set()
    for label in used_labels:
        key = label_to_key.get(label)
        if key and key not in seen:
            keys.append(key)
            seen.add(key)

    return keys


def _user_is_sensitivity_restricted(result):
    """
    Mirror masks.py: a user is sensitivity-restricted if a "Sensitized" or
    "Compromised Barrier" skin state is present, OR "sensitivity" is a top concern.
    Using the same signal keeps product and mask gating consistent.
    """
    state_names = {s.get("state") for s in result.get("skin_states", [])}
    if state_names & _SENSITIVITY_STATES:
        return True
    return "sensitivity" in (result.get("top_concerns") or [])


def _attach_product_matches(result):
    """
    Attach curated Product recommendations to the result, grouped by ingredient.

    Read-only. For each recommended ingredient key, find active Products for that
    key, then filter by skin-type fit and (if the user is sensitivity-restricted)
    sensitivity-safety. Ingredients with no surviving product are omitted entirely,
    so the template renders nothing for them — we never fabricate a product.

    Builds result["product_matches"] = [
        {"ingredient_key": k, "ingredient_label": <label or key>,
         "products": [<Product>, ...]}, ...
    ]
    """
    keys = _ingredient_keys_from_result(result)
    if not keys:
        result["product_matches"] = []
        return result

    skin_type = result.get("skin_type", "")
    restrict_to_safe = _user_is_sensitivity_restricted(result)

    # ONE query for every relevant ingredient_key, grouped in Python — avoids an
    # N+1 loop. Ordered so the in-Python grouping yields cheapest-first, then name.
    products = list(
        Product.objects.filter(is_active=True, ingredient_key__in=keys)
    )

    # Group surviving products by ingredient_key after applying the two filters.
    by_key = {}
    for product in products:
        # SENSITIVITY: when restricted, keep only sensitivity-safe products.
        if restrict_to_safe and not product.sensitivity_safe:
            continue

        # SKIN TYPE: empty compatible list = all types; otherwise must contain the
        # user's skin type.
        compatible = product.get_compatible_types_list()
        if compatible and skin_type not in compatible:
            continue

        by_key.setdefault(product.ingredient_key, []).append(product)

    # Label lookup for the heading (fall back to the key if no DB label exists).
    ingredient_db = get_ingredient_db()

    matches = []
    for key in keys:  # preserve recommendation order
        group = by_key.get(key)
        if not group:
            continue  # no surviving product for this ingredient -> render nothing

        # Cheapest-first, then name. Unknown tiers sort last via the .get default.
        group.sort(key=lambda p: (_BUDGET_ORDER.get(p.budget_tier, 99), p.name))

        label = (ingredient_db.get(key) or {}).get("label") or key
        matches.append({
            "ingredient_key":   key,
            "ingredient_label": label,
            "products":         group,
        })

    result["product_matches"] = matches
    return result


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

    # Attach curated Product matches. Done here on the SUCCESS path so BOTH
    # confirm_result (fresh) and my_routine (regenerated) get products with no
    # extra wiring at either call site.
    _attach_product_matches(result)

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
        # routine_start_date is intentionally NOT set here — it is owned by the
        # start_routine action. Omitting it leaves new rows null and preserves any
        # existing value when a returning user re-analyses.
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


@login_required
def my_routine(request):
    """
    Regenerate the user's saved routine WITHOUT re-running the quiz.

    Rebuilds the original QueryDict from the profile's stored raw_input and
    reuses _run_full_analysis, so the regenerated result is identical to the
    original analysis. This is read-only: it does NOT persist (re-writing would
    be redundant and could clobber routine_start_date semantics).
    """
    profile = UserSkinProfile.objects.filter(linked_user=request.user).first()

    # No profile, or an empty/blank raw_input (e.g. a pre-Brief-01.5 row that
    # never re-analysed) -> nothing to regenerate from. Send them to the quiz.
    if profile is None or not profile.raw_input:
        return redirect("skin_form")

    # Rebuild the exact QueryDict the engine originally consumed. setlist
    # preserves multi-value fields, so .getlist("skin_goals"/"concerns") returns
    # every value and the regenerated routine matches the original analysis.
    qd = QueryDict("", mutable=True)
    for key, values in profile.raw_input.items():
        qd.setlist(key, values)

    result = _run_full_analysis(qd)

    # A legacy/corrupt raw_input could fail validation — don't 500, re-quiz.
    if result.get("error"):
        return redirect("skin_form")

    return render(request, "skin_profile/result.html", result)


@login_required
def start_routine(request):
    """
    Stamp routine_start_date = now() on the user's profile.

    Used by both the "Start Routine" and "Restart" buttons on the dashboard.
    POST-only: it mutates state, so a GET simply falls through to the dashboard
    redirect without writing anything.
    """
    if request.method == "POST":
        profile = UserSkinProfile.objects.filter(linked_user=request.user).first()
        if profile is not None:
            profile.routine_start_date = timezone.now()
            # Narrow write — only the two columns we touch. "updated_at" must be
            # listed explicitly: auto_now only fires for fields named in
            # update_fields on a partial save.
            profile.save(update_fields=["routine_start_date", "updated_at"])

    return redirect("dashboard")
