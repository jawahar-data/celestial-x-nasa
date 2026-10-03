# CELESTIAL X — Package init
from .database   import init_database, get_connection, get_stats
from .config     import load_api_key, save_api_key, validate_api_key, get_key_status, mask_key
from .ingestion  import fetch_raw, store_raw, generate_demo_observations, REGION_BBOXES, PRODUCTS, PRODUCT_TO_SAT
from .harmonizer import harmonize_dataframe, harmonize_and_store, get_harmonized_dataframe
from .fire_fuse  import (
    run_fire_fuse, get_events_dataframe, get_event_timeline,
    get_event_observations, get_event_h3_cells, benchmark_h3_vs_naive,
    DEFAULT_CONFIG, close_inactive_events,
)
from .risk       import assess_all_events, get_risk_map_data, compute_risk_score, RISK_COLOR_MAP
from .reports    import (
    generate_event_report, generate_pending_reports,
    get_all_reports, get_report_content,
)

__all__ = [
    "init_database", "get_connection", "get_stats",
    "load_api_key", "save_api_key", "validate_api_key", "get_key_status", "mask_key",
    "fetch_raw", "store_raw", "generate_demo_observations", "REGION_BBOXES", "PRODUCTS",
    "harmonize_dataframe", "harmonize_and_store", "get_harmonized_dataframe",
    "run_fire_fuse", "get_events_dataframe", "get_event_timeline",
    "get_event_observations", "get_event_h3_cells", "benchmark_h3_vs_naive",
    "DEFAULT_CONFIG", "close_inactive_events",
    "assess_all_events", "get_risk_map_data", "compute_risk_score", "RISK_COLOR_MAP",
    "generate_event_report", "generate_pending_reports",
    "get_all_reports", "get_report_content",
]
