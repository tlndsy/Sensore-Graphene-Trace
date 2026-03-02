# patient/views.py
from django.shortcuts import render
from django.utils import timezone
from user.models import PressureMapReading, ReadingEquipment
from patient.utils.pressure_calculations import load_csv_frames, process_frame
import tempfile, os

def upload_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        equipment = ReadingEquipment.objects.first()  # adjust as needed

        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            for chunk in csv_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        frames = load_csv_frames(tmp_path)

        for frame in frames:
            peak, contact = process_frame(frame)
            PressureMapReading.objects.create(
                pressure_reading=csv_file.name,
                peak_pressure=peak,
                contact_area=contact,  # ← note: it's contact_area not contact_area_percent in their model
                reading_equipment=equipment,
            )

        os.unlink(tmp_path)
        return render(request, 'success.html', {'count': len(frames)})

    return render(request, 'upload.html')