"""
Unit tests for CELESTIAL X Potential Fire Spread & Downwind Exposure Intelligence
"""
import unittest
from celestial.fire_spread import (
    _destination_point,
    assess_fire_spread_and_exposure,
)

class TestFireSpread(unittest.TestCase):
    def test_destination_point(self):
        """Verify spherical destination point propagation."""
        lat, lon = _destination_point(11.0, 76.0, 0.0, 111.0)
        self.assertEqual(round(lat, 1), 12.0)
        self.assertEqual(round(lon, 1), 76.0)

    def test_assess_fire_spread_exposure(self):
        """Verify downwind spread assessment creates proper radii and bearings."""
        weather = {
            "wind_speed_kmh": 25.0,
            "wind_direction_deg": 90.0,  # East wind -> blows West (270°)
            "wind_cardinal": "E",
        }
        env = {
            "slope_deg": 15.0,
            "aspect_deg": 270.0,
            "fuel_flammability": 75,
        }
        res = assess_fire_spread_and_exposure(
            event_id="EVT-TEST",
            centroid_lat=11.6,
            centroid_lon=76.5,
            peak_frp=120.0,
            mean_frp=65.0,
            weather_dict=weather,
            env_dict=env
        )

        self.assertIn("downwind_bearing_deg", res)
        self.assertEqual(res["downwind_bearing_deg"], 270.0)
        self.assertEqual(res["downwind_cardinal"], "W")
        self.assertIn("estimated_ros_proxy_kmh", res)
        self.assertIn("potential_exposure_radius_24h_km", res)
        self.assertGreater(res["spread_potential_index"], 0.0)

if __name__ == "__main__":
    unittest.main()
