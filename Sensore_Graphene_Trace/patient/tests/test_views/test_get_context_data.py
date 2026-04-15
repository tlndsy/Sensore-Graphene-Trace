from patient.views import PressureDataView
from patient.mixins import PatientTestSetupMixin

class PatientGetContextDataViewTests(PatientTestSetupMixin):
    def test_get_context_data_with_data(self):
        request = self.factory.get("/")
        request.user = self.patient
        response = PressureDataView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("metric_data", response.context_data)

    def test_get_context_data_with_no_data(self):
        self.reading.delete()
        request = self.factory.get("/")
        request.user = self.patient
        response = PressureDataView.as_view()(request)
        self.assertIn("metric_data", response.context_data)