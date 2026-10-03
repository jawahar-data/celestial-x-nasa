"""
CELESTIAL X — Configuration & API Key Management
==================================================
Handles one-time NASA API key setup, validation, and persistent storage
via a local .env file. The key is NEVER exposed in frontend JavaScript,
NEVER committed to git, and NEVER logged.

Usage
-----
    from celestial.config import load_api_key, save_api_key, validate_api_key

Security notes
--------------
- Key stored in .env (must be in .gitignore)
- Only the last 4 characters displayed in Settings UI
- .env.example contains a placeholder only
"""

import os
import re
import requests
from pathlib import Path

# Project root (one level up from this file's directory)
PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE     = PROJECT_ROOT / ".env"
ENV_EXAMPLE  = PROJECT_ROOT / ".env.example"

# NASA FIRMS validation endpoint
FIRMS_BASE   = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

# Small test region (India, 1-day) used for key validation
_VALIDATION_BBOX    = "77.0,28.0,78.0,29.0"
_VALIDATION_PRODUCT = "MODIS_NRT"
_VALIDATION_DAYS    = 1


def _ensure_env_example() -> None:
    """Create .env.example with a placeholder if it does not exist."""
    if not ENV_EXAMPLE.exists():
        ENV_EXAMPLE.write_text(
            "# CELESTIAL X — Environment Variables\n"
            "# Copy this file to .env and fill in your real values.\n"
            "# NEVER commit .env to git.\n\n"
            "NASA_API_KEY=your_nasa_firms_api_key_here\n"
        )


def _ensure_gitignore() -> None:
    """Ensure .env is in .gitignore."""
    gitignore = PROJECT_ROOT / ".gitignore"
    lines = gitignore.read_text().splitlines() if gitignore.exists() else []
    entries = [".env", "celestial_x.db", "__pycache__/", "*.pyc", ".DS_Store"]
    changed = False
    for entry in entries:
        if entry not in lines:
            lines.append(entry)
            changed = True
    if changed:
        gitignore.write_text("\n".join(lines) + "\n")


def load_api_key() -> str | None:
    """
    Load the NASA API key from .env file.
    Returns None if the key is not set or is the placeholder value.
    """
    env_path = ENV_FILE
    if not env_path.exists():
        return None
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line.startswith("NASA_API_KEY="):
            val = line.split("=", 1)[1].strip().strip('"').strip("'")
            if val and val != "your_nasa_firms_api_key_here":
                return val
    return None


def save_api_key(key: str) -> None:
    """
    Save the NASA API key to .env file.
    Creates .env if it does not exist, updates existing entry if it does.
    """
    _ensure_env_example()
    _ensure_gitignore()
    key = key.strip()
    env_path = ENV_FILE
    if env_path.exists():
        lines = env_path.read_text().splitlines()
        new_lines = []
        found = False
        for line in lines:
            if line.strip().startswith("NASA_API_KEY="):
                new_lines.append(f"NASA_API_KEY={key}")
                found = True
            else:
                new_lines.append(line)
        if not found:
            new_lines.append(f"NASA_API_KEY={key}")
        env_path.write_text("\n".join(new_lines) + "\n")
    else:
        env_path.write_text(
            "# CELESTIAL X — Environment Variables (DO NOT COMMIT)\n"
            f"NASA_API_KEY={key}\n"
        )


def mask_key(key: str | None) -> str:
    """Return a masked version showing only the last 4 characters."""
    if not key:
        return "Not configured"
    if len(key) <= 4:
        return "****"
    return "·" * (len(key) - 4) + key[-4:]


def validate_api_key(key: str) -> tuple[bool, str]:
    """
    Validate the key by making a real (small) request to NASA FIRMS.
    Returns (is_valid: bool, message: str).
    Does NOT store or log the key.
    """
    if not key or not key.strip():
        return False, "No API key provided."
    key = key.strip()
    url = f"{FIRMS_BASE}/{key}/{_VALIDATION_PRODUCT}/{_VALIDATION_BBOX}/{_VALIDATION_DAYS}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            text = r.text.strip()
            if "invalid" in text.lower() or "unauthorized" in text.lower() or "error" in text.lower():
                return False, f"FIRMS API rejected the key: {text[:100]}"
            return True, "API key validated successfully against NASA FIRMS."
        elif r.status_code == 401:
            return False, "Invalid API key (HTTP 401 Unauthorized)."
        elif r.status_code == 429:
            return False, "Rate limited — key appears valid but too many requests."
        else:
            return False, f"Unexpected response from FIRMS API: HTTP {r.status_code}"
    except requests.exceptions.Timeout:
        return False, "Validation timed out. Check network connectivity."
    except requests.exceptions.ConnectionError:
        return False, "Cannot reach NASA FIRMS API. Check network connectivity."
    except Exception as exc:
        return False, f"Validation error: {exc}"


def get_key_status() -> dict:
    """Return a status dict for the Settings page."""
    key = load_api_key()
    return {
        "configured": key is not None,
        "masked":     mask_key(key),
        "key":        key,          # full key — only used server-side, never sent to browser
    }


if __name__ == "__main__":
    _ensure_env_example()
    _ensure_gitignore()
    status = get_key_status()
    print(f"API Key configured: {status['configured']}")
    print(f"Masked:             {status['masked']}")
