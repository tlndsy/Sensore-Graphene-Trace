# patient/views.py
from datetime import timedelta

from django.core.files.base import ContentFile
from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
import numpy as np
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

import pandas as pd
import tempfile, os, csv, io

from Sensore_Graphene_Trace import global_constants as constants

from user.models import User, Message, PressureMapReading, ReadingEquipment, ProductInfo
from patient.utils.pressure_calculations import load_csv_frames, process_frame, calculate_contact_area_percent
from patient.scaninterpreter import ScanInterpreter
from .mixins import BasePatientMixin
from . import forms

# Create your views here.
@login_required(login_url='/user/home/')
def patient_home_OLD(request):
    user = request.user
    # Check if the user belongs to the 'Patient' group
    if not user.groups.filter(name=constants.PATIENT).exists():
        return HttpResponseForbidden("403 Forbidden: You do not have permission to access this page.")

    # Get number of notifications for the user
    num_notifications = len(Message.objects.filter(recipient=user, read_receipt=False))

    context = {"user": user, "num_notifications": num_notifications}

    return render(request, 'patient/patient_home.html', context)

class PatientHomeView(BasePatientMixin, TemplateView):
    template_name = "patient/patient_home.html"

@login_required(login_url='/user/home/')
def view_devices_OLD(request):
    user = request.user
    if not user.groups.filter(name=constants.PATIENT).exists():
        return HttpResponseForbidden("403 Forbidden: You do not have permission to access this page.")

    # Get number of notifications for the user
    num_notifications = len(Message.objects.filter(recipient=user, read_receipt=False))

    devices = ReadingEquipment.objects.filter(user=user)
    context = {"devices": devices, "num_notifications": num_notifications}
    return render(request, 'patient/patient_view_devices.html', context)

class PatientViewDevices(BasePatientMixin, TemplateView):
    template_name = "patient/patient_view_devices.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["devices"] = ReadingEquipment.objects.filter(user=self.request.user)

        return context

@login_required(login_url='/user/home/')
def register_device_OLD(request):
    user = request.user
    if not user.groups.filter(name=constants.PATIENT).exists():
        return HttpResponseForbidden("403 Forbidden: You do not have permission to access this page.")

    if request.method == 'POST':
        form = forms.RegisterDevice(request.POST, request.FILES)
        if form.is_valid():
            new_device = form.save(commit=False)
            new_device.user = user
            new_device.save()
            return redirect('user:patient:viewDevices')
    else:
        form = forms.RegisterDevice()

    num_notifications = len(Message.objects.filter(recipient=user, read_receipt=False))
    context = {"form": form, "user": user, "num_notifications": num_notifications}
    return render(request, 'patient/patient_register_device.html', context)

class PatientRegisterDeviceView(BasePatientMixin, CreateView):
    form_class = forms.RegisterDevice
    template_name = "patient/patient_register_device.html"
    success_url = reverse_lazy("user:patient:viewDevices")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

def stats(request):
    return HttpResponse("This is the patients stats page (e.g., graph, heatmap")

def interpreterDisplay(request, reportNumber = 0):
    user = request.user
    from user.models import Report

    all_readings = (PressureMapReading.objects.filter(reading_equipment__user=user).all())
    all_readings = all_readings.order_by('timestamp')
    noOfReadings = len(all_readings)
    interpreter = ScanInterpreter()

    # Check if requested report is within limits
    reportNumber = interpreter.checkReportInRange(reportNumber, noOfReadings)

    try:
        current_reading = all_readings[reportNumber]
        file = current_reading.pressure_reading

    except Exception:  # If no scans found, inform user of this
        context = interpreter.returnEmptyPage()
        return render(request, "patient\interpreterDisplay.html", context)

    if not Report.objects.filter(pressure_map_reading=current_reading).exists():
        # Make a new report only if one does not already exist
        report = interpreter.generate_report(current_reading)
    else:
        report = Report.objects.filter(pressure_map_reading=current_reading).last()

    report.read_receipt = True
    report.save()

    frameHeatmap = interpreter.get_pressure_matrix(file, report.frame)
    reportContents = report.content.split("@")

    scanTime = all_readings[reportNumber].timestamp

    context = {"report_0": reportContents[0], "report_1": reportContents[1], "report_2": reportContents[2],
               "reportNumber": reportNumber+1, "noOfReports": noOfReadings,
               "heatmapArr": frameHeatmap, "allReports": all_readings, "user": user, "scanTime": scanTime}

    return render(request, "patient\interpreterDisplay.html", context)


def profile(request):
    return HttpResponse("This is the patients profile page")

def notifications(request):
    return HttpResponse("This is the patients notification page")

def messages(request):
    return HttpResponse("This is the patients messaging page")

class PressureDataView(BasePatientMixin, TemplateView):
    template_name = "patient/patient_view_pressure_data.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get users pressure mat information
        latest_reading = (PressureMapReading.objects.filter(reading_equipment__user=self.request.user).order_by('-timestamp').first())
        if not latest_reading or not latest_reading.metrics: context["metric_data"] = empty_context()  # Return empty if no data
        try: context["metric_data"] = process_metrics(latest_reading)
        except Exception as e:  # Error reading pressure mat data
            print("Error reading patient csv:", e)
            context["metric_data"] = empty_context()
        return context

@login_required(login_url='/user/home/')
def OLD_Pressure_Data_View(request):
    # Authentication
    if not request.user.groups.filter(name=constants.PATIENT).exists:
        return redirect("home") # Redirect users without login
    else: user = request.user # Request the correct user

    # Get users pressure mat information
    latest_reading = (PressureMapReading.objects.filter(reading_equipment__user=user).order_by('-timestamp').first())
    if not latest_reading or not latest_reading.metrics:
        return render(request, "patient/patient_view_pressure_data.html", empty_context()) # Return empty if no data
    try:
        metric_data = process_metrics(latest_reading)
    except Exception as e: # Error reading pressure mat data
        print("Error reading patient csv:", e)
        return render(request, "patient/patient_view_pressure_data.html", empty_context())
    return render(request, "patient/patient_view_pressure_data.html", {"metric_data":metric_data})

def process_metrics(latest_reading):
    fps = latest_reading.reading_equipment.product_info.refresh_rate  # Frames per second
    start_time = latest_reading.timestamp

    with latest_reading.metrics.open(mode='r') as f:  # Read metrics csv
        df = pd.read_csv(f)  # Copy csv to pandas dataframe

    # Calculate values to display per second
    df['second'] = np.floor((df['frame'] / fps)).astype(int)  # approx. 15 fps
    df['time'] = pd.to_datetime(start_time) + pd.to_timedelta(df['second'], unit='s')
    df['time_sec'] = df['time'].dt.floor('s')

    metrics = ["peak_pressure","mean_pressure","std_pressure","peak_pressure_index","coefficient_of_variation", "contact_area","contact_area_percent","cop_x","cop_y"]
    metrics_per_sec = df.groupby('time_sec')[metrics].mean() # Take the mean from 15 frames
    aggregated_metrics_per_sec = {metric: metrics_per_sec[metric].tolist() for metric in metrics} # Aggregate
    times = metrics_per_sec.index.tolist() # Store the seconds recorded
    return {"pressure_frames": get_all_pressure_matrix_frames(latest_reading), **aggregated_metrics_per_sec,"times":times,"flat_pressure_matrix": get_pressure_matrix(latest_reading)}
    
def empty_context():
    return {"pressure_frames":[], "peak_pressure":[],"contact_area":[],"times":[],"flat_pressure_matrix":[], "mean_pressure":[],"std_pressure":[],"contact_area_percent":[], "cop_x":[],"cop_y":[], "coefficient_of_variation":[] }

# Takes the latest reading and converts the pressure data into a list
def get_pressure_matrix(latest_reading):
    pressure_matrix = []
    if latest_reading.pressure_reading:
        width = latest_reading.reading_equipment.product_info.resolution_width
        height = latest_reading.reading_equipment.product_info.resolution_height
        total_cells = width * height
        with latest_reading.pressure_reading.open(mode='r') as f:
            reader = csv.reader(f)
            for row in reader:
                pressure_matrix.extend([float(value) for value in row])
        pressure_matrix += [0.0] * (total_cells - len(pressure_matrix))
        pressure_matrix = pressure_matrix[:total_cells]
    return pressure_matrix

# Gets all the pressure matrix frames from the most recent pressure reading file
def get_all_pressure_matrix_frames(latest_reading):
    frames = []
    if not latest_reading.pressure_reading:
        return frames
    width = latest_reading.reading_equipment.product_info.resolution_width
    height = latest_reading.reading_equipment.product_info.resolution_height
    with latest_reading.pressure_reading.open(mode='r') as f:
        df = pd.read_csv(f)
    data = df.values.tolist()
    FRAME_SIZE = height
    for i in range(0, len(data), FRAME_SIZE):
        block = data[i:i + FRAME_SIZE]
        if len(block) < FRAME_SIZE:
            break  # skip incomplete frame
        frame = [val for row in block for val in row]
        frames.append(frame)
    return frames


def temp_logout(request):
    if request.method == 'POST':
        logout(request)
        return redirect("user:home")

def upload_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        print(f"File received: {csv_file.name}")

        equipment = ReadingEquipment.objects.first()
        print(f"Equipment: {equipment}")

        if not equipment:
            return render(request, 'patient/upload.html', {'error': 'No equipment found.'})

        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            for chunk in csv_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        frames = load_csv_frames(tmp_path)
        print(f"Frames loaded: {len(frames)}")
        os.unlink(tmp_path)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['frame', 'peak_pressure', 'contact_area'])

        results = []
        for i, frame in enumerate(frames):
            peak, contact = process_frame(frame)
            writer.writerow([i + 1, peak, contact])
            results.append((peak, contact))

        csv_content = output.getvalue().encode('utf-8')
        csv_filename = f"results_{csv_file.name}"

        try:
            reading = PressureMapReading(
                reading_equipment=equipment,
                peak_pressure=max(r[0] for r in results),
                contact_area=max(r[1] for r in results),
            )
            reading.pressure_reading.save(
                csv_filename,
                ContentFile(csv_content),
                save=True
            )
            print(f"Saved reading ID: {reading.id}")
        except Exception as e:
            print(f"ERROR saving: {e}")
            return render(request, 'patient/upload.html', {'error': str(e)})

        return render(request, 'patient/success.html', {'count': len(frames)})

    return render(request, 'patient/upload.html')
