# patient/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.base import ContentFile
from user.models import PressureMapReading
from patient.utils.pressure_calculations import load_csv_frames, process_frame
import tempfile, os, csv, io


@receiver(post_save, sender=PressureMapReading)
def process_pressure_map(sender, instance, created, **kwargs):
    # Only process newly created records that have a CSV but no metrics yet
    if created and instance.pressure_reading and not instance.peak_pressure:

        # Save CSV temporarily to disk
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            for chunk in instance.pressure_reading.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        frames = load_csv_frames(tmp_path)
        os.unlink(tmp_path)

        # Calculate metrics per frame
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['frame', 'peak_pressure', 'contact_area'])

        results = []
        for i, frame in enumerate(frames):
            peak, contact = process_frame(frame)
            writer.writerow([i + 1, peak, contact])
            results.append((peak, contact))

        # Save results CSV back to the same record
        csv_content = output.getvalue().encode('utf-8')
        csv_filename = f"metrics_{instance.pressure_reading.name.split('/')[-1]}"

        # Update the record with metrics
        PressureMapReading.objects.filter(pk=instance.pk).update(
            peak_pressure=max(r[0] for r in results),
            contact_area=max(r[1] for r in results),
        )

        # Save metrics CSV to a separate field if you add one
        # OR overwrite the existing file
        instance.pressure_reading.save(
            csv_filename,
            ContentFile(csv_content),
            save=False
        )
        PressureMapReading.objects.filter(pk=instance.pk).update(
            pressure_reading=instance.pressure_reading.name
        )

        print(f"Processed {len(frames)} frames for reading {instance.pk}")
