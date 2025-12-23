#!/usr/bin/env python3
"""Check that TODOs and FIXMEs have ticket references."""
import re
import sys
from pathlib import Path


def check_file(filepath):
    """Check a single file for TODOs without ticket references."""
    content = Path(filepath).read_text()
    lines = content.split("\n")

    # Pattern: TODO or FIXME without ticket reference like TODO(#123) or FIXME: T-456
    todo_pattern = r"#\s*(TODO|FIXME)\b(?![\(\[])"

    violations = []
    for line_num, line in enumerate(lines, 1):
        if re.search(todo_pattern, line, re.IGNORECASE):
            violations.append((line_num, line.strip()))

    return violations


def main():
    """Check all staged Python files."""
    if len(sys.argv) < 2:
        sys.exit(0)

    all_violations = []

    for filepath in sys.argv[1:]:
        if not filepath.endswith(".py"):
            continue

        violations = check_file(filepath)
        if violations:
            all_violations.append((filepath, violations))

    if all_violations:
        print("❌ Found TODOs/FIXMEs without ticket references:")
        print()
        for filepath, violations in all_violations:
            print(f"📄 {filepath}:")
            for line_num, line in violations:
                print(f"   Line {line_num}: {line}")
            print()

        print("Please use one of these formats:")
        print("  - TODO(#123): Description")
        print("  - FIXME[T-456]: Description")
        print("  - TODO: Implement feature (tracked in issue #789)")
        sys.exit(1)

    print("✅ All TODOs have ticket references")
    sys.exit(0)


if __name__ == "__main__":
    main()
