"""Generate openapi.json by importing and introspecting the FastAPI app.

Usage:
    python scripts/generate_openapi.py [--output ../openapi.json]
"""

import json
import sys
from pathlib import Path

# Ensure the api package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import app  # noqa: E402

OUTPUT = Path(__file__).resolve().parent.parent / "openapi.json"


def main() -> None:
    path = OUTPUT
    if len(sys.argv) > 1 and sys.argv[1] == "--output":
        path = Path(sys.argv[2])

    schema = app.openapi()
    path.write_text(json.dumps(schema, indent=2))
    print(f"✓ OpenAPI schema written to {path}")


if __name__ == "__main__":
    main()
