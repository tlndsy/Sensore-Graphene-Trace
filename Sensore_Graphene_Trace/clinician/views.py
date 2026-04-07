from django.shortcuts import render


# Create your views here.
def reportDisplay(request, reportNumber = 0, patientNumber = 0):
    user = request.user
    from user.models import PatientClinician
    from user.models import Report
    from user.models import PressureMapReading
    from patient.scaninterpreter import ScanInterpreter

    try:
        patientCliniciansList = (PatientClinician.objects.filter(clinician=user).all())
        patientClinician = patientCliniciansList[patientNumber]
        patient = patientClinician.patient

        all_readings = (PressureMapReading.objects.filter(reading_equipment__user=patient).all())
        all_readings = all_readings.order_by('timestamp')
        noOfReadings = len(all_readings)

    except Exception:
        reportContents = ["", "", "", ""]

        reportContents[0] = "There has been an error identifying this patient."
        reportContents[1] = "Please contact your administrator for assistance."

        context = {"report_0": reportContents[0], "report_1": reportContents[1], "report_2": reportContents[2],
                   "report_3": reportContents[3], "reportNumber": 0, "noOfReports": 0, "allReports": []}
        return render(request, "clinician/clinicianReportDisplay.html", context)

    # Check if requested report is within limits
    if reportNumber >= noOfReadings:
        reportNumber = noOfReadings

    try:
        current_reading = all_readings[reportNumber]
        file = current_reading.pressure_reading

        if not Report.objects.filter(pressure_map_reading=current_reading).exists():
            # Make a new report only if one does not already exist
            report = Report(pressure_map_reading=current_reading)
            reportContents, scanNumber = ScanInterpreter.runInterpreter(ScanInterpreter, file)
            report.content = "@".join(reportContents)
            report.frame = scanNumber
            report.save()
        else:
            report = Report.objects.filter(pressure_map_reading=current_reading).last()

        frameHeatmap = ScanInterpreter.get_pressure_matrix(ScanInterpreter, file, report.frame)  # Currently not working
        reportContents = report.content.split("@")

        context = {"report_0": reportContents[0], "report_1": reportContents[1], "report_2": reportContents[2],
                   "report_3": reportContents[3], "reportNumber": reportNumber + 1, "noOfReports": noOfReadings,
                   "heatmap": frameHeatmap, "allReports": all_readings, "patientNumber": patientNumber,
                   "listOfPatients": patientCliniciansList}

    except Exception:  # If no scans found, inform user of this
        reportContents = ["", "", "", ""]

        reportContents[0] = "No scans have been detected for this patient."
        reportContents[1] = "Please contact your administrator if you believe this is in error."

        context = {"report_0": reportContents[0], "report_1": reportContents[1], "report_2": reportContents[2],
                   "report_3": reportContents[3], "reportNumber": 0, "noOfReports": 0, "allReports": all_readings}


    return render(request, "clinician/clinicianReportDisplay.html", context)

def displayProfile(request):
    user = request.user
    from user.models import PatientClinician

    #Obtain patient/clinicians
    patientCliniciansList = (PatientClinician.objects.filter(clinician=user).all())

    context = {"listOfPatients": patientCliniciansList}
    return render(request, "clinician/clinicianProfile.html", context)

def tempLogout(request): #Just redirects the user to their home page for now
    context = {}
    return render(request, "clinician/clinicianProfile.html", context)