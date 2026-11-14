"""
Unit tests for CELESTIAL X SQLite Database Schema & Audit Logging
"""
import unittest
from celestial.database import (
    init_database, get_connection, log_ai_query,
    update_data_source_metadata, get_stats
)

class TestDatabase(unittest.TestCase):
    def setUp(self):
        init_database()

    def test_database_tables_exist(self):
        """Verify all 14 required tables exist in the database."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {r[0] for r in cur.fetchall()}
        conn.close()

        expected_tables = {
            "raw_observations",
            "harmonized_observations",
            "fire_events",
            "event_observations",
            "event_h3_cells",
            "risk_predictions",
            "reports",
            "api_configuration",
            "weather_observations",
            "environmental_context",
            "fire_spread_assessments",
            "risk_model_metadata",
            "ai_query_history",
            "data_source_metadata",
        }
        missing = expected_tables - tables
        self.assertFalse(missing, f"Missing tables in database: {missing}")

    def test_log_ai_query(self):
        """Verify AI Copilot query logging works and is auditable."""
        log_ai_query(
            user_query="Which fires are burning near Mudumalai?",
            sql_executed="SELECT * FROM environmental_context WHERE nearest_protected_area LIKE '%Mudumalai%';",
            response_text="Event EVT-TEST is 2.4 km from Mudumalai.",
            rows_returned=1,
            latency_ms=12.5
        )

        conn = get_connection()
        row = conn.execute("SELECT * FROM ai_query_history ORDER BY id DESC LIMIT 1;").fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertIn("Mudumalai", row["user_query"])

    def test_update_data_source_metadata(self):
        """Verify metadata update tracking for data provenance."""
        update_data_source_metadata(
            source_name="TEST_STAC_CATALOG",
            endpoint_url="https://planetarycomputer.microsoft.com/api/stac/v1",
            last_status="ACTIVE",
            quota_remaining=5000,
            error_count=0
        )

        conn = get_connection()
        row = conn.execute("SELECT * FROM data_source_metadata WHERE source_name='TEST_STAC_CATALOG';").fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row["last_status"], "ACTIVE")

if __name__ == "__main__":
    unittest.main()
