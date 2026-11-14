"""
Unit tests for CELESTIAL-X-RISK-v2 5-Pillar Scientific Risk Engine
"""
import unittest
from celestial.risk import (
    compute_risk_score,
    compute_risk_score_v2,
    _score_frp,
    _score_duration,
    _score_weather,
    _score_environment,
)

class TestRisk(unittest.TestCase):
    def test_thermal_intensity_scoring(self):
        """Verify FRP score scales appropriately between 0 and 1."""
        self.assertEqual(_score_frp(0, 0), 0.0)
        self.assertGreater(_score_frp(100, 50), 0.2)
        self.assertGreaterEqual(_score_frp(600, 400), 0.7)

    def test_risk_score_v2_composite(self):
        """Verify CELESTIAL-X-RISK-v2 calculates balanced 5-pillar weights."""
        event = {
            "event_id": "EVT-TEST-001",
            "centroid_lat": 11.6,
            "centroid_lon": 76.5,
            "peak_frp": 150.0,
            "mean_frp": 80.0,
            "duration_hours": 36.0,
            "observation_count": 12,
            "h3_cell_count": 5,
            "modis_count": 4,
            "viirs_count": 8,
            "max_confidence": 0.9,
        }
        weather = {
            "relative_humidity_pct": 20.0,
            "wind_speed_kmh": 28.0,
            "fosberg_index": 55.0,
        }
        environmental = {
            "slope_deg": 18.0,
            "flammability": 75,
            "protected_area_distance_km": 4.5,
        }

        score, level, breakdown = compute_risk_score_v2(event, weather, environmental)
        self.assertTrue(0.0 <= score <= 1.0)
        self.assertIn(level, ["LOW", "MODERATE", "HIGH", "VERY HIGH"])
        self.assertEqual(breakdown["model_version"], "CELESTIAL-X-RISK-v2")
        self.assertIn("thermal_intensity_score", breakdown)
        self.assertIn("persistence_expansion_score", breakdown)
        self.assertIn("weather_deficit_score", breakdown)
        self.assertIn("fuel_topography_score", breakdown)
        self.assertIn("conservation_proximity_score", breakdown)

    def test_backward_compatibility(self):
        """Verify legacy compute_risk_score function works without breaking."""
        event = {
            "peak_frp": 80.0,
            "mean_frp": 40.0,
            "duration_hours": 12.0,
            "h3_cell_count": 4,
            "modis_count": 2,
            "viirs_count": 6,
            "max_confidence": 0.85,
        }
        score, level = compute_risk_score(event)
        self.assertTrue(0.0 <= score <= 1.0)
        self.assertIn(level, ["LOW", "MODERATE", "HIGH", "VERY HIGH"])

if __name__ == "__main__":
    unittest.main()
