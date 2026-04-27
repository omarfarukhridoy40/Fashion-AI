from django.shortcuts import render

from .logic import run_skin_engine
from .masks import get_mask_recommendations
from .goals import build_goal_roadmap, get_goal_choices
from .routine import build_three_phase_plan


def skin_form(request):
    """
    Handles the main skin analysis form.

    GET  -> Show the empty form to the user.
    POST -> Run the engine, then show the confirmation screen first.
            If the user already confirmed, show the final result page.
    """

    # Pass goal choices to the form template so the checkboxes render
    goal_choices = get_goal_choices()

    if request.method == "POST":

        # Step 1 — Run the skin analysis engine
        result = run_skin_engine(request.POST)

        # Step 2 — If the engine found missing required data, show the form again with an error
        if result.get("error"):
            return render(request, "skin_profile/skin_form.html", {
                "form_error":   result["message"],
                "goal_choices": goal_choices,
            })

        # Step 3 — Get the user's selected skin goals from the form
        selected_goals = request.POST.getlist("skin_goals")

        # Step 4 — Build the goal roadmap
        goal_roadmap = build_goal_roadmap(
            selected_goals    = selected_goals,
            top_concerns      = result["top_concerns"],
            conflict_detected = result["conflict_detected"],
        )

        # Step 5 — Get face mask recommendations
        masks = get_mask_recommendations(
            skin_type    = result["skin_type"],
            top_concerns = result["top_concerns"],
            skin_states  = result["skin_states"],
        )

        # Step 6 — Build the three-phase plan
        has_dehydration = any(s["state"] == "Dehydrated" for s in result["skin_states"])

        three_phase_plan = build_three_phase_plan(
            skin_type         = result["skin_type"],
            skin_states       = result["skin_states"],
            top_concerns      = result["top_concerns"],
            conflict_detected = result["conflict_detected"],
            recommendation    = result["recommendation"],
            goal_roadmap      = goal_roadmap,
            has_dehydration   = has_dehydration,
        )

        # Step 7 — Attach everything to the result dictionary
        result["goal_roadmap"]      = goal_roadmap
        result["masks"]             = masks
        result["three_phase_plan"]  = three_phase_plan
        result["selected_goals"]    = selected_goals

        # Step 8 — Route based on confirmation status
        if not request.POST.get("confirmed"):
            return render(request, "skin_profile/confirm.html", result)

        return render(request, "skin_profile/result.html", result)

    return render(request, "skin_profile/skin_form.html", {
        "goal_choices": goal_choices,
    })


def confirm_result(request):
    """
    Called when the user clicks 'Yes show my routine' on the confirmation screen.
    Runs the engine again with the same data and shows the result.
    """
    if request.method == "POST":

        result = run_skin_engine(request.POST)

        selected_goals = request.POST.getlist("skin_goals")

        goal_roadmap = build_goal_roadmap(
            selected_goals    = selected_goals,
            top_concerns      = result["top_concerns"],
            conflict_detected = result["conflict_detected"],
        )

        masks = get_mask_recommendations(
            skin_type    = result["skin_type"],
            top_concerns = result["top_concerns"],
            skin_states  = result["skin_states"],
        )

        has_dehydration = any(s["state"] == "Dehydrated" for s in result["skin_states"])

        three_phase_plan = build_three_phase_plan(
            skin_type         = result["skin_type"],
            skin_states       = result["skin_states"],
            top_concerns      = result["top_concerns"],
            conflict_detected = result["conflict_detected"],
            recommendation    = result["recommendation"],
            goal_roadmap      = goal_roadmap,
            has_dehydration   = has_dehydration,
        )

        result["goal_roadmap"]      = goal_roadmap
        result["masks"]             = masks
        result["three_phase_plan"]  = three_phase_plan
        result["selected_goals"]    = selected_goals

        return render(request, "skin_profile/result.html", result)

    return render(request, "skin_profile/skin_form.html", {
        "goal_choices": get_goal_choices(),
    })
