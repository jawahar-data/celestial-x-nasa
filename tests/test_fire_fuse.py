"""
Unit tests for CELESTIAL X FIRE-FUSE Spatiotemporal Reconciliation Engine
"""
import unittest
from celestial.fire_fuse import (
    _haversine_km,
    run_fire_fuse,
    get_events_dataframe,
    DEFAULT_CONFIG,
)

class TestFireFuse(unittest.TestCase):
    def test_haversine_distance(self):
        """Verify Haversine formula calculation for known points."""
        d = _haversine_km(13.0827, 80.2707, 12.9716, 77.5946)
        self.assertTrue(280.0 < d < 305.0)

        d_zero = _haversine_km(11.5, 76.5, 11.5, 76.5)
        self.assertEqual(d_zero, 0.0)

    def test_run_fire_fuse_audit(self):
        """Verify that reconciliation executes and returns audit metrics."""
        audit = run_fire_fuse()
        self.assertIsInstance(audit, dict)
        self.assertIn("raw_hotspot_count", audit)
        self.assertIn("harmonized_observation_count", audit)
        self.assertIn("persistent_event_count", audit)
        self.assertIn("obs_duplicates_filtered", audit)
        self.assertIn("duplicate_detection_reduction_pct", audit)
        self.assertGreaterEqual(audit["duplicate_detection_reduction_pct"], 0.0)

    def test_spatial_temporal_thresholds(self):
        """Verify standard thresholds comply with scientific requirements (<= 15 km, <= 36 hrs)."""
        self.assertLessEqual(DEFAULT_CONFIG["SPATIAL_THRESHOLD_KM"], 15.0)
        self.assertLessEqual(DEFAULT_CONFIG["TEMPORAL_THRESHOLD_HRS"], 36.0)

if __name__ == "__main__":
    unittest.main()
