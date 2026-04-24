from django.shortcuts import render


# Create your views here.
def reportDisplay(request, reportNumber = 0, patientNumber = 0):
    user = request.user
    from user.models import PatientClinician
    from user.models import Report
    from user.models import PressureMapReading
    from patient.scaninterpreter import ScanInterpreter

    #Create instance of the ScanInterpreter class
    interpreter = ScanInterpreter()

    try:
        # Retrieve list of patient/clinician links with this clinician, then retrieve relevant one from list
        patientCliniciansList = (PatientClinician.objects.filter(clinician=user).all())
        patientClinician = patientCliniciansList[patientNumber]
        patient = patientClinician.patient

        # Retrieve list of pressure map readings assigned to this patient
        all_readings = (PressureMapReading.objects.filter(reading_equipment__user=patient).all())
        all_readings = all_readings.order_by('timestamp')
        noOfReadings = len(all_readings)
    except Exception:
        # Return error page if data retrieval fails
        context = interpreter.returnEmptyPage()
        return render(request, "clinician/clinicianReportDisplay.html", context)

    # Check if requested report is within limits
    reportNumber = interpreter.checkReportInRange(reportNumber, noOfReadings)

    try:
        # Take desired pressure map reading from list of readings
        current_reading = all_readings[reportNumber]
        file = current_reading.pressure_reading

        if not Report.objects.filter(pressure_map_reading=current_reading).exists():
            # Make a new report only if one does not already exist
            report = interpreter.generate_report(current_reading)
        else:
            # Retrieve report from database
            report = Report.objects.filter(pressure_map_reading=current_reading).last()

        # Retrieve heatmap and list of report contents
        frameHeatmap = interpreter.get_pressure_matrix(file, report.frame)
        reportContents = report.content.split("@")

        # Retrieve time scan is made
        scanTime = all_readings[reportNumber].timestamp

        # Construct context dictionary to pass into HTML page
        context = {"report_0": reportContents[0], "report_1": reportContents[1], "report_2": reportContents[2],
                   "report_3": reportContents[3], "reportNumber": reportNumber + 1, "noOfReports": noOfReadings,
                   "heatmapArr": frameHeatmap, "allReports": all_readings, "patientNumber": patientNumber,
                   "listOfPatients": patientCliniciansList, "user": user, "patient": patient, "scanTime": scanTime}

    except Exception:  # If no scans found, return error page
        context = interpreter.returnEmptyPage()

    return render(request, "clinician/clinicianReportDisplay.html", context)

def displayProfile(request):
    user = request.user
    from user.models import PatientClinician

    #Obtain patient/clinicians
    patientCliniciansList = (PatientClinician.objects.filter(clinician=user).all())

    context = {"listOfPatients": patientCliniciansList, "user": user}
    return render(request, "clinician/clinicianProfile.html", context)

def tempLogout(request): #Just redirects the user to their home page for now
    context = {}
    return render(request, "clinician/clinicianProfile.html", context)