from django.shortcuts import render, HttpResponse

from user.models import PressureMapReading, ReadingEquipment


# Create your views here.
def stats(request):
    return HttpResponse("This is the patients stats page (e.g., graph, heatmap")

def interpreterDisplay(request):
    user = request.user

    scanData = PressureMapReading.objects.filter(reading_equipment__user=user)
    try:
        file = scanData.pressure_reading.url
    except (Exception):
        file = " "

    report = interpreterDisplay(file)

    context = {"report", report}
    return render (request, "interpreterDisplay.html", context)