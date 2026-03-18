# patient/views.py
from datetime import timedelta

from django.core.files.base import ContentFile
from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
import pandas as pd
import numpy as np
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

import pandas as pd
import tempfile, os, csv, io

from Sensore_Graphene_Trace import global_constants as constants

from user.models import User, Message, PressureMapReading, ReadingEquipment
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

def interpreterDisplay(request):
    user = request.user

    latest_reading = (PressureMapReading.objects.filter(reading_equipment__user=user).latest('timestamp'))

    file = latest_reading.pressure_reading

    report = ScanInterpreter.runInterpreter(ScanInterpreter, file)

    context = {"report_0": report[0], "report_1": report[1], "report_2": report[2]}
    return render(request, "patient\interpreterDisplay.html", context)

def profile(request):
    return HttpResponse("This is the patients profile page")

def notifications(request):
    return HttpResponse("This is the patients notification page")

def messages(request):
    return HttpResponse("This is the patients messaging page")

def view_graph(request):
    seconds = []; peak_pressure = []; contact_area = []; times = []; pressure_matrix = []
    try: # Try read the latest pressure mat data
        user = request.user # Request the correct user
        latest_reading = (PressureMapReading.objects.filter(reading_equipment__user=user).order_by('-timestamp').first())
        fps = latest_reading.reading_equipment.product_info.refresh_rate # Frames per second
        start_time = latest_reading.timestamp

        if latest_reading and latest_reading.metrics: # If the latest reading exists
            with latest_reading.metrics.open(mode='r') as f: # Read metrics csv
                df = pd.read_csv(f) # Copy csv to pandas dataframe

            # Calculate values to display per second
            df['second'] = np.floor((df['frame'] / fps)).astype(int) # approx. 15 fps
            df['time'] = pd.to_datetime(start_time) + pd.to_timedelta(df['second'], unit='s')
            df['time_sec'] = df['time'].dt.floor('s')

            # Aggregate
            peak_pressure_per_s = df.groupby('time_sec')['peak_pressure'].max()
            contact_area_per_s = df.groupby('time_sec')['contact_area'].mean()

            # Align with the time of the reading
            times = peak_pressure_per_s.index.tolist()

            #Convert to lists for the graph
            seconds = peak_pressure_per_s.index.tolist() # Each index represents a second
            peak_pressure = peak_pressure_per_s.values.tolist()
            contact_area = contact_area_per_s.values.tolist()
            flat_pressure_matrix = get_pressure_matrix(latest_reading, pressure_matrix)

    except Exception as e: # Error reading pressure mat data
        print("Error reading patient csv:", e)
    #print("Seconds:", seconds)
    #print("Peak pressure:", peak_pressure)
    #print("Pressure matrix:", pressure_matrix)
    return render(request, "patientGraph.html",
                  {"seconds":seconds,"peak_pressure":peak_pressure,"contact_area":contact_area, "times":times,"flat_pressure_matrix": flat_pressure_matrix})

# Takes the latest reading and converts the pressure data into a list
def get_pressure_matrix(latest_reading, pressure_matrix):
    if latest_reading.pressure_reading:
        with latest_reading.pressure_reading.open(mode='r') as f:
            reader = csv.reader(f)
            for row in reader: pressure_matrix.extend([float(value) for value in row])
        pressure_matrix += [0.0] * (1024 - len(pressure_matrix))
        pressure_matrix = pressure_matrix[:1024]
    return pressure_matrix

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
