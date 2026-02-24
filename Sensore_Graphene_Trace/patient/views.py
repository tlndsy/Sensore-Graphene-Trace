from django.shortcuts import render, HttpResponse

from user.models import PressureMapReading, ReadingEquipment
from patient.scaninterpreter import ScanInterpreter


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

    report = ScanInterpreter.runInterpreter(ScanInterpreter, file)

    context = {"report_0": report[0], "report_1": report[1], "report_2": report[2]}
    return render (request, "patient\interpreterDisplay.html", context)