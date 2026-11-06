"""Freeze inputs, validate lineage and resume a single local research run.

No scheduled workers or financial transactions. Core ingestion owns its journal;
this runner owns checkpoints and immutable input/precondition checks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import lineage
import research

ROOT = Path(__file__).resolve().parents[1]
PHASES = ("prepared", "ingested", "lineage_validated", "built", "verified", "complete")


def _path(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        raise ValueError("Use a repository-relative POSIX path")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Path escapes repository")
    result = (Path(root) / path).resolve()
    if not result.is_relative_to(Path(root).resolve()):
        raise ValueError("Resolved path escapes repository")
    return result


def _raw(path):
    # Portable across Git's LF/CRLF checkouts; no other content normalization.
    return Path(path).read_bytes().replace(b"\r\n", b"\n")


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _write(path, value):
    research._atomic_write(path, (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def _inputs(root, manifest):
    excluded = {f"data/{key}.json" for key in research.CORE_KEYS}
    result = {}
    for path in lineage.input_paths(root, manifest):
        relative = path.relative_to(root).as_posix()
        if relative not in excluded:
            result[relative] = _sha(_raw(path))
    return result


def _coverage(manifest, batch):
    spec = research.read_json(manifest)
    for key in ("sources", "claims"):
        if spec.get("registries", {}).get(key, {}).get("path") != f"data/{key}.json":
            raise ValueError("Pipeline lineage registries must match ingestion's data/sources.json and data/claims.json")
    covered = set(spec.get("scope", {}).get("claims", []))
    missing = {c["id"] for c in batch.get("claims", [])} - covered
    if missing:
        raise ValueError("Batch claims missing from lineage scope: " + ", ".join(sorted(missing)))


def _load_plan(root, plan_path):
    path = _path(root, plan_path)
    envelope = research.read_json(path)
    plan = envelope["plan"]
    if envelope.get("sha256") != research._state_hash(plan) or plan.get("version") != 1:
        raise ValueError("Frozen plan checksum/version mismatch")
    run_id = plan.get("run_id", "")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,95}", run_id):
        raise ValueError("Invalid frozen run ID")
    if path != _path(root, f"runs/pipeline/{run_id}/plan.json"):
        raise ValueError("Plan location does not match its run ID")
    batch = _path(root, plan["batch"])
    if batch != path.parent / "batch.json" or _sha(batch.read_bytes()) != plan["batch_sha256"]:
        raise ValueError("Frozen batch changed (including line endings); restore its exact original LF bytes before resuming a pending run")
    manifest = _path(root, plan["lineage"])
    if _inputs(root, manifest) != plan["input_sha256"]:
        raise ValueError("Frozen lineage input changed; prepare a new run, do not overwrite this plan")
    _coverage(manifest, research.read_json(batch))
    return path, envelope


def _checkpoint(path, envelope, phase):
    if path.exists():
        state = research.read_json(path)
        if state.get("plan_sha256") != envelope["sha256"] or state.get("phase") not in PHASES:
            raise ValueError("Checkpoint is invalid or belongs to a different plan")
        if PHASES.index(state["phase"]) >= PHASES.index(phase):
            return
    _write(path, {"plan_sha256": envelope["sha256"], "phase": phase})


def prepare(root, run_id, batch_path, manifest_path):
    root = Path(root).resolve()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,95}", run_id):
        raise ValueError("Run ID must be 1-96 letters, digits, underscores or hyphens")
    batch = _path(root, batch_path)
    manifest = _path(root, manifest_path)
    relative_plan = f"runs/pipeline/{run_id}/plan.json"
    path = _path(root, relative_plan)
    # Different lock namespace from ingestion. Locks are local and cooperative.
    with research.writer_lock(root / ".pipeline"):
        raw = _raw(batch)
        if path.exists():
            _, envelope = _load_plan(root, relative_plan)
            plan = envelope["plan"]
            if plan["batch_sha256"] != _sha(raw) or plan["lineage"] != manifest_path:
                raise ValueError("Run ID already belongs to different inputs; use a new run ID")
            return {"status": "already_prepared", "plan": relative_plan}
        before = research.load(root)
        batch_value = json.loads(raw.decode("utf-8-sig"))
        after = research._merge(before, batch_value)
        lineage.validate(root, manifest, data_override=after)
        _coverage(manifest, batch_value)
        plan = {
            "version": 1, "run_id": run_id,
            "batch": f"runs/pipeline/{run_id}/batch.json", "batch_sha256": _sha(raw),
            "lineage": manifest_path, "input_sha256": _inputs(root, manifest),
            "input_hash_policy": "SHA256 of UTF-8 file bytes with CRLF normalized to LF",
            "expected_before_sha256": research._state_hash(before),
            "expected_after_sha256": research._state_hash(after),
        }
        frozen = path.parent / "batch.json"
        if frozen.exists() and _raw(frozen) != raw:
            raise ValueError("Orphan frozen batch differs; preserve it and use a new run ID")
        research._atomic_write(frozen, raw)
        envelope = {"sha256": research._state_hash(plan), "plan": plan}
        _write(path, envelope)
        _checkpoint(path.parent / "state.json", envelope, "prepared")
        return {"status": "prepared", "plan": relative_plan}


def apply(root, plan_path):
    root = Path(root).resolve()
    with research.writer_lock(root / ".pipeline"):
        path, envelope = _load_plan(root, plan_path)
        plan = envelope["plan"]
        state_path = path.parent / "state.json"
        _checkpoint(state_path, envelope, "prepared")
        if not research.has_pending(root):
            before = research.load(root)
            after = research._merge(before, research.read_json(_path(root, plan["batch"])))
            if research._state_hash(before) not in {plan["expected_before_sha256"], plan["expected_after_sha256"]}:
                raise ValueError("Stale plan: current research has changed; prepare a new run")
            if research._state_hash(after) != plan["expected_after_sha256"]:
                raise ValueError("Proposed after-state differs from the frozen plan")
            lineage.validate(root, _path(root, plan["lineage"]), data_override=after)
        # Pending core writes resume only from this exact frozen batch. Core
        # checks both hashes under its own lock, closing the preflight race.
        research.ingest(root, _path(root, plan["batch"]),
                        expected_before_sha256=plan["expected_before_sha256"],
                        expected_after_sha256=plan["expected_after_sha256"])
        _checkpoint(state_path, envelope, "ingested")
        summary = lineage.validate(root, _path(root, plan["lineage"]))
        _checkpoint(state_path, envelope, "lineage_validated")
        research.build(root)
        _checkpoint(state_path, envelope, "built")
        current = research.load(root)
        research.assert_valid(current)
        if research._state_hash(current) != plan["expected_after_sha256"]:
            raise ValueError("Research changed before verification; completion was not acknowledged")
        broken = research.check_links(root)
        if broken:
            raise ValueError("Broken local links:\n" + "\n".join(broken))
        _load_plan(root, plan_path)  # Do not acknowledge changed inputs mid-run.
        _checkpoint(state_path, envelope, "verified")
        _checkpoint(state_path, envelope, "complete")
        return {"status": "complete", "run_id": plan["run_id"],
                "data_sha256": plan["expected_after_sha256"], "lineage": summary}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--run-id", required=True)
    p.add_argument("--batch", required=True)
    p.add_argument("--lineage", required=True)
    p = sub.add_parser("apply")
    p.add_argument("--plan", required=True)
    args = parser.parse_args()
    try:
        result = prepare(args.root, args.run_id, args.batch, args.lineage) if args.command == "prepare" else apply(args.root, args.plan)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"Pipeline stopped: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
