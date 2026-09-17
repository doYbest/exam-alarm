"""Export or verify the committed API contract."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.main import app


def main() -> int:
    target = ROOT / "contracts/openapi.json"
    content = json.dumps(app.openapi(), ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if "--check" in sys.argv:
        if not target.exists() or target.read_text(encoding="utf-8") != content:
            print("contracts/openapi.json 与当前 API 不一致", file=sys.stderr)
            return 1
        return 0
    target.write_text(content, encoding="utf-8")
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
