# patient/views.py
from django.shortcuts import render
from django.core.files.base import ContentFile
from user.models import PressureMapReading, ReadingEquipment
from patient.utils.pressure_calculations import load_csv_frames, process_frame
import tempfile, os, csv, io

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
