# patient/management/commands/process_csv.py
import os
from django.core.management.base import BaseCommand
from django.utils import timezone
from user.models import PressureMapReading, ReadingEquipment
from patient.utils.pressure_calculations import load_csv_frames, process_frame



class Command(BaseCommand):
    help = 'Process a pressure map CSV and store results in the database'

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str, help='Path to the CSV file')
        parser.add_argument('--equipment_id', type=int, default=1)

    def handle(self, *args, **options):
        filepath = options['csv_path']
        equipment_id = options['equipment_id']

        if not os.path.exists(filepath):
            self.stderr.write(f"File not found: {filepath}")
            return

        equipment = ReadingEquipment.objects.get(id=equipment_id)
        frames = load_csv_frames(filepath)

        self.stdout.write(f"Processing {len(frames)} frames from {filepath}...")

        for i, frame in enumerate(frames):
            peak, contact = process_frame(frame)

            PressureMapReading.objects.create(
                pressure_reading=filepath,
                timestamp=timezone.now(),
                peak_pressure=peak,
                contact_area_percent=contact,
                reading_equipment=equipment,
            )

            self.stdout.write(
                f"  Frame {i+1}: Peak={peak}, Contact Area={contact}%"
            )

        self.stdout.write(self.style.SUCCESS(f"Done! {len(frames)} records saved."))
