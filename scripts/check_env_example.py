#!/usr/bin/env python3
"""Check that .env.example contains all required settings."""
import re
import sys
from pathlib import Path


def get_required_settings():
    """Extract required settings from settings.py."""
    settings_file = Path("src/config/settings.py")

    if not settings_file.exists():
        print("❌ settings.py not found")
        return set()

    content = settings_file.read_text()

    # Find all Field(..., description="...") patterns (required fields)
    required_pattern = r"(\w+):\s+\w+\s*=\s*Field\(\s*\.\.\."
    required_fields = set(re.findall(required_pattern, content))

    return required_fields


def get_env_example_vars():
    """Extract variables from .env.example."""
    env_example = Path(".env.example")

    if not env_example.exists():
        print("❌ .env.example not found")
        return set()

    content = env_example.read_text()

    # Find all VARIABLE_NAME= patterns
    vars_pattern = r"^([A-Z_]+)="
    env_vars = set(re.findall(vars_pattern, content, re.MULTILINE))

    return env_vars


def main():
    """Check if .env.example is in sync with settings.py."""
    required = get_required_settings()
    env_vars = get_env_example_vars()

    if not required or not env_vars:
        sys.exit(1)

    # Convert required field names to ENV_VAR format
    required_env = {field.upper() for field in required}

    missing = required_env - env_vars

    if missing:
        print("❌ .env.example is missing required variables:")
        for var in sorted(missing):
            print(f"   - {var}")
        print("\nPlease update .env.example to include all required settings.")
        sys.exit(1)

    print("✅ .env.example contains all required settings")
    sys.exit(0)


if __name__ == "__main__":
    main()
