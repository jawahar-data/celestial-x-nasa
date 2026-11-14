"""
Unit tests for CELESTIAL X Atmospheric Weather Intelligence Module
"""
import unittest
from celestial.weather_intelligence import (
    calculate_fosberg_fire_weather_index,
    get_wind_cardinal_direction,
    get_climatological_weather_fallback,
    get_weather_for_location,
)

class TestWeather(unittest.TestCase):
    def test_deg_to_cardinal(self):
        """Verify cardinal direction conversion."""
        self.assertEqual(get_wind_cardinal_direction(0), "N")
        self.assertEqual(get_wind_cardinal_direction(360), "N")
        self.assertEqual(get_wind_cardinal_direction(90), "E")
        self.assertEqual(get_wind_cardinal_direction(180), "S")
        self.assertEqual(get_wind_cardinal_direction(270), "W")
        self.assertEqual(get_wind_cardinal_direction(45), "NE")
        self.assertEqual(get_wind_cardinal_direction(135), "SE")

    def test_fosberg_index_extreme_fire_weather(self):
        """Verify Fosberg FFWI increases with high temp, low RH, and strong wind."""
        ffwi_high = calculate_fosberg_fire_weather_index(temp_c=38.0, rh_pct=15.0, wind_kmh=35.0)
        ffwi_low = calculate_fosberg_fire_weather_index(temp_c=20.0, rh_pct=85.0, wind_kmh=5.0)

        self.assertTrue(0.0 <= ffwi_low <= 100.0)
        self.assertTrue(0.0 <= ffwi_high <= 100.0)
        self.assertGreater(ffwi_high, ffwi_low)
        self.assertGreater(ffwi_high, 40.0)

    def test_climatological_baseline_fallback(self):
        """Verify ERA5 climatological fallback produces valid weather parameters."""
        weather = get_climatological_weather_fallback(lat=11.6, lon=76.5, dt_iso="2024-03-15T12:00:00")
        self.assertIn("temperature_c", weather)
        self.assertIn("relative_humidity_pct", weather)
        self.assertIn("wind_speed_kmh", weather)
        self.assertIn("fire_weather_index", weather)
        self.assertIn("CLIMATOLOGY", weather["source"])
        self.assertEqual(weather["is_forecast"], 0)

if __name__ == "__main__":
    unittest.main()
