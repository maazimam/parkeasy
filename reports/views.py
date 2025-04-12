from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from .forms import ReportForm
from messaging.models import Message
from listings.models import Listing


@login_required
def report_item(request, content_type_str, object_id):
    # Map string identifiers to actual models
    content_type_map = {
        "message": Message,
        "listing": Listing,
        # Add other reportable models here
    }

    if content_type_str not in content_type_map:
        return redirect("home")

    model = content_type_map[content_type_str]
    content_type = ContentType.objects.get_for_model(model)

    # Check if the object exists
    try:
        reported_object = model.objects.get(pk=object_id)

        # Permission check for messages - only sender or recipient can report
        if content_type_str == "message":
            if (
                request.user != reported_object.sender
                and request.user != reported_object.recipient
            ):
                return redirect("inbox")

    except model.DoesNotExist:
        if content_type_str == "message":
            return redirect("inbox")
        else:
            return redirect("home")

    if request.method == "POST":
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.content_type = content_type
            report.object_id = object_id
            report.save()

            # Store the success message in the session
            request.session["success_message"] = (
                "Thank you for your report. Our team will review it shortly."
            )

            # Redirect based on content type
            if content_type_str == "message":
                return redirect("inbox")
            elif content_type_str == "listing":
                return redirect("view_listings")
    else:
        form = ReportForm()

    context = {
        "form": form,
        "reported_object": reported_object,
        "content_type_str": content_type_str,
    }

    return render(request, "reports/report_form.html", context)
