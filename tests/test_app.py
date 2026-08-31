import unittest

import app as fluids_app


class FluidsAppTests(unittest.TestCase):
    def setUp(self):
        fluids_app.app.config.update(TESTING=True, SECRET_KEY="test")
        self.client = fluids_app.app.test_client()

    def test_home_page_has_browser_local_management(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Thermodynamic Fluids Explorer", response.data)
        self.assertIn(b"Customize your fluid list", response.data)
        self.assertIn(b"Reset to all defaults", response.data)
        self.assertIn(b"Suggestions and bug reports", response.data)
        self.assertIn(b"https://formspree.io/f/xjyvggnl", response.data)
        self.assertIn(b'name="_gotcha"', response.data)
        self.assertIn(b'data-scroll-to="manage-fluids"', response.data)
        self.assertIn(b'data-scroll-to="feedback"', response.data)
        self.assertNotIn(b'target="_blank"', response.data)
        self.assertNotIn(b"Methoxyethanol", response.data)

    def test_custom_fluid_validation(self):
        response = self.client.post("/api/fluids/validate", json={"identifier": "acetone", "name": "My acetone"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["cas_number"], "67-64-1")
        self.assertEqual(response.json["name"], "My acetone")

    def test_browser_added_fluid_can_be_calculated(self):
        response = self.client.post("/", data={
            "mode": "single", "unit": "K", "start_temperature": "298.15",
            "pressure": "101325", "fluids": "67-64-1", "fluid_labels": "My acetone",
            "properties": "Density (kg/m^3)",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"My acetone", response.data)

    def test_water_range_matches_expected_density(self):
        response = self.client.post("/", data={
            "mode": "range", "unit": "K", "start_temperature": "298.15",
            "end_temperature": "300", "pressure": "101325", "points": "2",
            "fluids": "7732-18-5", "properties": "Density (kg/m^3)",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"997.", response.data)
        self.assertIn(b"2 calculated data points", response.data)

    def test_csv_export(self):
        response = self.client.post("/export", data={
            "mode": "single", "unit": "K", "start_temperature": "298.15",
            "pressure": "101325", "fluids": "7732-18-5",
            "properties": "Density (kg/m^3)",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/csv")

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "ok"})

    def test_public_point_limit(self):
        response = self.client.post("/", data={
            "mode": "range", "unit": "K", "start_temperature": "298.15",
            "end_temperature": "300", "pressure": "101325", "points": "101",
            "fluids": "7732-18-5", "properties": "Density (kg/m^3)",
        })
        self.assertIn(b"Number of points must be between 2 and 100", response.data)


if __name__ == "__main__":
    unittest.main()
