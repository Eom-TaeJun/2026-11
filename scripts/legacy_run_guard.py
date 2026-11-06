"""Stop archived, dated one-off helpers before their former body can mutate data."""
import json
import sys
from pathlib import Path


def stop_archived_run(root, run_id):
    """Always exits; this guard never interprets new inputs as already applied."""
    try:
        record = json.loads((Path(root) / "runs" / f"{run_id}.json").read_text(encoding="utf-8-sig"))
        if record.get("run_id") != run_id or record.get("status") != "published_content_verified":
            raise ValueError("archive is not confirmed published")
    except (OSError, ValueError, TypeError) as exc:
        print(f"Archived helper stopped: {exc}. Preserve the files and use run_pipeline.py for a new run.", file=sys.stderr)
        raise SystemExit(1) from exc
    print(json.dumps({"status": "archived_noop", "run_id": run_id,
                      "message": "Published run preserved. No new inputs were processed. Use run_pipeline.py with a new run ID."}))
    raise SystemExit(0)
