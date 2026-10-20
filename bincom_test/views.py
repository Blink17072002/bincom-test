from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect
from django.db.models import Sum, Max
from django.utils import timezone

from .models import AnnouncedPuResults, PollingUnit, Lga, Party, Ward


# Create your views here.

def home(request):
    return render(request, "bincom_test/home.html")


def polling_unit_result(request):
    polling_units = PollingUnit.objects.order_by("uniqueid")
    selected_id = request.GET.get("uniqueid")
    results = []
    selected_unit = None

    if selected_id:
        selected_unit = PollingUnit.objects.filter(uniqueid=selected_id).first()
        results = AnnouncedPuResults.objects.filter(polling_unit_uniqueid=str(selected_id)).order_by("party_abbreviation")

    context = {
        "polling_units": polling_units,
        "selected_id": selected_id,
        "selected_unit": selected_unit,
        "results": results,
    }
    return render(request, "bincom_test/polling_unit_result.html", context=context)


def lga_result(request):
    lgas = Lga.objects.only("uniqueid", "lga_id", "lga_name", "state_id").order_by("lga_name")
    selected_lga_id = request.GET.get("lga_id")
    selected_lga = None
    totals = []
    unit_count = 0
    units_with_results = 0

    if selected_lga_id:
        selected_lga = Lga.objects.only("uniqueid", "lga_id", "lga_name").filter(lga_id=selected_lga_id).first()
        units = PollingUnit.objects.filter(lga_id=selected_lga_id)
        unit_ids = [str(unit.uniqueid) for unit in units]
        unit_count = len(unit_ids)

        totals = (
            AnnouncedPuResults.objects.filter(polling_unit_uniqueid__in=unit_ids)
            .values("party_abbreviation")
            .annotate(total=Sum("party_score"))
            .order_by("party_abbreviation")
        )

        units_with_results = (
            AnnouncedPuResults.objects.filter(polling_unit_uniqueid__in=unit_ids)
            .values("polling_unit_uniqueid").distinct().count()
        )

    context = {
        "lgas": lgas,
        "selected_lga_id": selected_lga_id,
        "selected_lga": selected_lga,
        "totals": totals,
        "unit_count": unit_count,
        "units_with_results": units_with_results,
    }
    return render(request, "bincom_test/lga_result.html", context=context)


def new_polling_unit_result(request):
    lgas = Lga.objects.only("uniqueid", "lga_id", "lga_name").order_by("lga_name")
    wards = Ward.objects.only("uniqueid", "ward_id", "ward_name", "lga_id").order_by("ward_name")
    parties = Party.objects.order_by("id")

    if request.method == "POST":
        lga_id = request.POST.get("lga_id")
        ward_uniqueid = request.POST.get("ward_uniqueid")
        unit_name = (request.POST.get("polling_unit_name") or "").strip()
        unit_number = (request.POST.get("polling_unit_number") or "").strip()
        entered_by = (request.POST.get("entered_by_user") or "web").strip() or "web"

        ward = Ward.objects.only("uniqueid", "ward_id", "lga_id").filter(uniqueid=ward_uniqueid).first()
        lga = Lga.objects.only("lga_id").filter(lga_id=lga_id).first()

        if not unit_name or not ward or not lga:
            messages.error(request, "Choose an LGA, a ward, and enter a polling unit name.")
        elif str(ward.lga_id) != str(lga.lga_id):
            messages.error(request, "That ward does not belong to the selected LGA.")
        else:
            scores = []
            invalid = False
            for party in parties:
                raw = request.POST.get(f"score_{party.id}", "0").strip() or "0"
                try:
                    score = int(raw)
                    if score < 0:
                        raise ValueError
                except ValueError:
                    invalid = True
                    break
                scores.append((party.partyid[:4], score))

            if invalid:
                messages.error(request, "All party scores must be whole numbers 0 or greater.")
            else:
                ip_address = request.META.get("REMOTE_ADDR") or "127.0.0.1"
                now = timezone.now()
                next_unit_id = (
                    PollingUnit.objects.filter(lga_id=lga.lga_id, ward_id=ward.ward_id)
                    .aggregate(mx=Max("polling_unit_id"))
                    .get("mx")
                    or 0
                ) + 1

                with transaction.atomic():
                    unit = PollingUnit.objects.create(
                        polling_unit_id=next_unit_id,
                        ward_id=ward.ward_id,
                        lga_id=lga.lga_id,
                        uniquewardid=ward.uniqueid,
                        polling_unit_number=unit_number or None,
                        polling_unit_name=unit_name,
                        entered_by_user=entered_by,
                        date_entered=now,
                        user_ip_address=ip_address,
                    )
                    for abbreviation, score in scores:
                        AnnouncedPuResults.objects.create(
                            polling_unit_uniqueid=str(unit.uniqueid),
                            party_abbreviation=abbreviation,
                            party_score=score,
                            entered_by_user=entered_by,
                            date_entered=now,
                            user_ip_address=ip_address,
                        )

                messages.success(
                    request,
                    f"Saved results for {unit_name} (unique ID {unit.uniqueid}).",
                )
                return redirect(f"/polling-unit/?uniqueid={unit.uniqueid}")

    context = {
        "lgas": lgas,
        "wards": wards,
        "parties": parties,
    }
    return render(request, "bincom_test/new_polling_unit_result.html", context=context)