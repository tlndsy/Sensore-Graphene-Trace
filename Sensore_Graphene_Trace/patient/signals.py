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
    if created and instance.pressure_reading and not instance.metrics:

        try:
            # Save raw CSV temporarily to disk
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
                for chunk in instance.pressure_reading.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name

            frames = load_csv_frames(tmp_path)
            os.unlink(tmp_path)

            if not frames:
                print(f"No frames found for reading {instance.pk}")
                return

            # Calculate metrics per frame
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['frame', 'peak_pressure', 'contact_area'])

            results = []
            for i, frame in enumerate(frames):
                peak, contact = process_frame(frame)
                writer.writerow([i + 1, peak, contact])
                results.append((peak, contact))

            # Save metrics CSV to metrics field
            csv_content = output.getvalue().encode('utf-8')
            csv_filename = f"metrics_{instance.pressure_reading.name.split('/')[-1]}"

            # Save to metrics field
            reading = PressureMapReading.objects.get(pk=instance.pk)
            reading.metrics.save(
                csv_filename,
                ContentFile(csv_content),
                save=True
            )

            print(f" Processed {len(frames)} frames for reading {instance.pk}")
            print(f"   Overall Peak: {max(r[0] for r in results)}, Max Contact: {max(r[1] for r in results)}")

        except Exception as e:
            print(f" Signal error for reading {instance.pk}: {e}")
            import traceback
            traceback.print_exc()