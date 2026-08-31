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
        self.assertIn(b'draggable="true"', response.data)
        self.assertIn(b"Your custom fluid order was saved", response.data)
        self.assertIn(b"Customize your property list", response.data)
        self.assertIn(b"Sortable property list", response.data)
        self.assertIn(b"Surface Tension (N/m)", response.data)
        self.assertIn(b'value="pressure_range"', response.data)
        self.assertIn(b'value="temperature_pressure_surface" disabled', response.data)
        self.assertIn(b'name="pressure_unit" value="atm"', response.data)
        self.assertNotIn(b"Single state", response.data)
        self.assertIn(b"value / 101325", response.data)
        self.assertIn(b"value * 101325", response.data)

    def test_custom_fluid_validation(self):
        response = self.client.post("/api/fluids/validate", json={"identifier": "acetone", "name": "My acetone"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["cas_number"], "67-64-1")
        self.assertEqual(response.json["name"], "My acetone")

    def test_browser_added_fluid_can_be_calculated(self):
        response = self.client.post("/", data={
            "mode": "temperature_range", "unit": "K", "pressure_unit": "Pa",
            "start_temperature": "298.15", "end_temperature": "300", "points": "2",
            "start_pressure": "101325", "fluids": "67-64-1", "fluid_labels": "My acetone",
            "properties": "Density (kg/m^3)",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"My acetone", response.data)

    def test_water_range_matches_expected_density(self):
        response = self.client.post("/", data={
            "mode": "temperature_range", "unit": "K", "pressure_unit": "Pa",
            "start_temperature": "298.15", "end_temperature": "300", "start_pressure": "101325", "points": "2",
            "fluids": "7732-18-5", "properties": "Density (kg/m^3)",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"997.", response.data)
        self.assertIn(b"2 calculated data points", response.data)

    def test_catalog_property_can_be_calculated(self):
        response = self.client.post("/", data={
            "mode": "temperature_range", "unit": "K", "pressure_unit": "Pa",
            "start_temperature": "298.15", "end_temperature": "300", "points": "2",
            "start_pressure": "101325", "fluids": "7732-18-5",
            "properties": "Surface Tension (N/m)",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Surface Tension (N/m)", response.data)
        self.assertIn(b"0.07197", response.data)

    def test_pressure_range_at_fixed_temperature_in_atmospheres(self):
        response = self.client.post("/", data={
            "mode": "pressure_range", "unit": "C", "pressure_unit": "atm",
            "start_temperature": "25", "start_pressure": "1", "end_pressure": "2",
            "points": "3", "fluids": "7732-18-5",
            "properties": "Density (kg/m^3)",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"3 calculated data points", response.data)
        self.assertIn(b"Pressure (atm)", response.data)
        self.assertIn(b'"x_label": "Pressure (atm)"', response.data)

    def test_three_dimensional_mode_is_reserved_but_not_enabled(self):
        response = self.client.post("/", data={
            "mode": "temperature_pressure_surface", "unit": "K", "pressure_unit": "Pa",
            "start_temperature": "298.15", "start_pressure": "101325", "points": "3",
            "fluids": "7732-18-5", "properties": "Density (kg/m^3)",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"surface mode is scaffolded but not available yet", response.data)

    def test_csv_export(self):
        response = self.client.post("/export", data={
            "mode": "temperature_range", "unit": "K", "pressure_unit": "Pa",
            "start_temperature": "298.15", "end_temperature": "300", "points": "2",
            "start_pressure": "101325", "fluids": "7732-18-5",
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
            "mode": "temperature_range", "unit": "K", "pressure_unit": "Pa",
            "start_temperature": "298.15", "end_temperature": "300", "start_pressure": "101325", "points": "101",
            "fluids": "7732-18-5", "properties": "Density (kg/m^3)",
        })
        self.assertIn(b"Number of points must be between 2 and 100", response.data)


if __name__ == "__main__":
    unittest.main()
