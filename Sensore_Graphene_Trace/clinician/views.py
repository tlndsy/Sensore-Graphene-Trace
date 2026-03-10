from django.shortcuts import render

# Create your views here.
def reportDisplay(request):
    context = {"report_0": "placeholder", "report_1": "placeholder2", "report_2": "placeholder3", "report_3": "placeholder4"}
    return render(request, "clinician/clinicianReportDisplay.html", context)