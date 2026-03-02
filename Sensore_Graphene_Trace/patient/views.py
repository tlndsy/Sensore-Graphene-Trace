# patient/views.py
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.utils import timezone

import tempfile, os, csv, io

from user.models import User, Message, PressureMapReading, ReadingEquipment
from patient.utils.pressure_calculations import load_csv_frames, process_frame
from patient.scaninterpreter import ScanInterpreter
from Sensore_Graphene_Trace import global_constants as constants
from . import forms


# Create your views here.
@login_required(login_url='/user/home/')
def home(request):
    user = request.user
    # Check if the user belongs to the 'Patient' group
    if not user.groups.filter(name='Patient').exists():
        return HttpResponseForbidden("403 Forbidden: You do not have permission to access this page.")

    # Get number of notifications for the user
    num_notifications = len(Message.objects.filter(recipient=user, read_receipt=False))

    context = {"user": user, "num_notifications": num_notifications}

    return render(request,'patient/home.html', context)


@login_required(login_url='/user/home/')
def viewDevices(request):
    user = request.user
    if not user.groups.filter(name=constants.PATIENT).exists():
        return HttpResponseForbidden("403 Forbidden: You do not have permission to access this page.")

    # Get number of notifications for the user
    num_notifications = len(Message.objects.filter(recipient=user, read_receipt=False))

    devices = ReadingEquipment.objects.filter(user=user)
    context = {"devices": devices, "num_notifications": num_notifications}
    return render(request, 'patient/viewDevices.html', context)

@login_required(login_url='/user/home/')
def registerDevice(request):
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
    return render(request, 'patient/registerDevice.html', context)

def stats(request):
    return HttpResponse("This is the patients stats page (e.g., graph, heatmap")

def interpreterDisplay(request):
    user = request.user

    latest_reading = (PressureMapReading.objects.filter(reading_equipment__user=user).latest('timestamp'))

    file = latest_reading.pressure_reading

    report = ScanInterpreter.runInterpreter(ScanInterpreter, file)

    context = {"report_0": report[0], "report_1": report[1], "report_2": report[2]}
    return render (request, "patient\interpreterDisplay.html", context)
  
def profile(request):
    return HttpResponse("This is the patients profile page")

def notifications(request):
    return HttpResponse("This is the patients notification page")

def messages(request):
    return HttpResponse("This is the patients messaging page")
  
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
