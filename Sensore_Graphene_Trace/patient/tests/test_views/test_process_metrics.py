from patient.views import process_metrics, get_pressure_matrix
from user.models import PressureMapReading
from django.core.files.uploadedfile import SimpleUploadedFile
from patient.mixins import PatientTestSetupMixin

class PatientProcessMetricsViewTests(PatientTestSetupMixin):
    def test_process_metrics_returns_expected_structure(self):
        csv_content = (
            "frame,peak_pressure,mean_pressure,std_pressure,cop_x,cop_y,"
            "contact_area,contact_area_percent,peak_pressure_index,coefficient_of_variation\n"
            "0,10,5,1,0.1,0.2,50,0.5,3,0.2\n"
            "1,12,6,1.1,0.2,0.3,52,0.52,4,0.21\n"
            "2,14,7,1.2,0.3,0.4,55,0.55,5,0.22\n"
        )
        file = SimpleUploadedFile("metrics.csv",csv_content.encode("utf-8"),content_type="text/csv")
        reading = PressureMapReading.objects.create(reading_equipment=self.equipment,metrics=file)
        result = process_metrics(reading)
        self.assertIn("times", result)
        self.assertIn("pressure_frames", result)
        self.assertIn("flat_pressure_matrix", result)
        self.assertIn("peak_pressure", result)
        self.assertIn("mean_pressure", result)
        self.assertIsInstance(result["peak_pressure"], list)
        self.assertIsInstance(result["times"], list)

    def test_process_metrics_empty_file(self):
        empty_csv = "frame,peak_pressure\n"
        file = SimpleUploadedFile("empty.csv",empty_csv.encode(),content_type="text/csv")
        reading = PressureMapReading.objects.create(reading_equipment=self.equipment,metrics=file)
        with self.assertRaises(Exception): process_metrics(reading)

    def test_get_pressure_matrix_exact_size(self):
        rows = [[i for i in range(10)] for _ in range(10)]
        file = self.create_csv_file(rows)
        reading = PressureMapReading.objects.create(reading_equipment=self.equipment,pressure_reading=file)
        matrix = get_pressure_matrix(reading)
        self.assertEqual(len(matrix), 100)
        self.assertEqual(matrix[0], 0.0)
        self.assertEqual(matrix[-1], 9.0)

    def test_get_pressure_matrix_padding(self):
        rows = [[1, 2, 3],[4, 5, 6]]
        file = self.create_csv_file(rows)
        reading = PressureMapReading.objects.create(reading_equipment=self.equipment,pressure_reading=file)
        matrix = get_pressure_matrix(reading)
        self.assertEqual(len(matrix), 100)
        self.assertEqual(matrix[0:6], [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        self.assertEqual(matrix[-1], 0.0)

    def test_get_pressure_matrix_truncation(self):
        rows = [[i for i in range(20)] for _ in range(20)]
        file = self.create_csv_file(rows)
        reading = PressureMapReading.objects.create(reading_equipment=self.equipment,pressure_reading=file)
        matrix = get_pressure_matrix(reading)
        self.assertEqual(len(matrix), 100)

    def test_pressure_matrix_no_file(self):
        reading = PressureMapReading.objects.create(reading_equipment=self.equipment)
        result = get_pressure_matrix(reading)
        self.assertEqual(result, [])