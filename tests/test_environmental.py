"""
Unit tests for CELESTIAL X Environmental Intelligence & Microsoft Planetary Computer STAC
"""
import unittest
from celestial.environmental_intelligence import (
    ESA_WORLDCOVER_CLASSES,
    calculate_environmental_sensitivity_score,
    find_nearest_protected_area,
)

class TestEnvironmental(unittest.TestCase):
    def test_esa_worldcover_matrix(self):
        """Verify ESA WorldCover class mappings and flammability scores."""
        tree = ESA_WORLDCOVER_CLASSES.get(10)
        self.assertIsNotNone(tree)
        self.assertEqual(tree["name"], "Tree cover")
        self.assertEqual(tree["flammability"], 75)

        water = ESA_WORLDCOVER_CLASSES.get(80)
        self.assertIsNotNone(water)
        self.assertEqual(water["flammability"], 0)

    def test_protected_area_proximity(self):
        """Verify distance calculation to known Western Ghats protected reserves."""
        name, dist, desig = find_nearest_protected_area(lat=11.60, lon=76.55)
        self.assertIn("Mudumalai", name)
        self.assertLess(dist, 15.0)

        name_far, dist_far, desig_far = find_nearest_protected_area(lat=13.08, lon=80.27)
        self.assertGreater(dist_far, 200.0)

    def test_environmental_sensitivity_score(self):
        """Verify ESI combines fuel, slope, and reserve proximity."""
        esi_high = calculate_environmental_sensitivity_score(
            flammability=75.0,
            slope_deg=25.0,
            dist_to_protected_km=2.0
        )
        esi_low = calculate_environmental_sensitivity_score(
            flammability=15.0,
            slope_deg=2.0,
            dist_to_protected_km=50.0
        )

        self.assertTrue(0.0 <= esi_low <= 100.0)
        self.assertTrue(0.0 <= esi_high <= 100.0)
        self.assertGreater(esi_high, esi_low)

if __name__ == "__main__":
    unittest.main()
