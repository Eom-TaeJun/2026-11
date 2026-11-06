"""Source-backed research records, wiki generation and retrieval. Python 3.11+, stdlib only."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import tempfile
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parents[1]
KINDS = {"fact", "institution_statement", "interpretation", "hypothesis", "unknown"}
READ_STATES = {"full_text", "selected_sections", "official_summary", "metadata_only", "unread"}
CORE_KEYS = ("sources", "claims", "topics")


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _state_hash(data):
    # Keep the canonicalization used by legacy history and pipeline plans.
    return _digest(json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8"))


def _text_bytes(text):
    return text.replace("\n", os.linesep).encode("utf-8")


def _json_bytes(value):
    return _text_bytes(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def _atomic_write(path, raw):
    """One-file replacement, not a multi-file commit; journals cover ingest."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)  # Only this invocation's temporary file.


@contextmanager
def writer_lock(root=ROOT):
    """Cooperative, local OS lock. Never delete the persistent lock file.

    Process exit releases the OS lock; an old file is not a stale held lock.
    This is not a distributed lock for synced/network copies of a checkout.
    """
    path = Path(root) / "history" / ".research.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        if path.stat().st_size == 0:
            stream.write(b"\0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise ValueError("Research writer is busy; retry after the current process exits. Do not delete its lock file.") from exc
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    _atomic_write(path, _json_bytes(value))


def load(root=ROOT):
    with writer_lock(root):
        _require_ready(root)
        return _load_unlocked(Path(root))


def _load_unlocked(root):
    return {key: read_json(root / "data" / f"{key}.json") for key in CORE_KEYS}


def errors(data):
    problems = []
    maps = {}
    for kind in ("sources", "claims", "topics"):
        records = data.get(kind)
        if not isinstance(records, list):
            problems.append(f"{kind}: list required")
            maps[kind] = {}
            continue
        indexed = {}
        for record in records:
            rid = record.get("id") if isinstance(record, dict) else None
            if not rid or not re.fullmatch(r"[A-Z][A-Z0-9-]*", rid):
                problems.append(f"{kind}: invalid ID {rid!r}")
                continue
            if rid in indexed:
                problems.append(f"{kind}: duplicate {rid}")
            indexed[rid] = record
        maps[kind] = indexed
    all_ids = [rid for group in maps.values() for rid in group]
    if len(all_ids) != len(set(all_ids)):
        problems.append("IDs must be unique across sources, claims and topics")
    for rid, topic in maps["topics"].items():
        for key in ("name", "question"):
            if not isinstance(topic.get(key), str) or not topic[key].strip():
                problems.append(f"{rid}: topic {key} required")
    urls = {}
    for rid, source in maps["sources"].items():
        for key in ("title", "publisher", "url", "checked_at", "read_status", "read_scope", "summary", "used_for", "limitations"):
            if not source.get(key):
                problems.append(f"{rid}: missing {key}")
        if source.get("visibility") != "public":
            problems.append(f"{rid}: public repository requires public evidence")
        parsed = urlparse(source.get("url", ""))
        if parsed.scheme != "https" or not parsed.netloc:
            problems.append(f"{rid}: public HTTPS URL required")
        url_key = source.get("url", "").rstrip("/")
        if url_key in urls:
            problems.append(f"{rid}: duplicate URL of {urls[url_key]}; update the existing record")
        urls[url_key] = rid
        if source.get("read_status") not in READ_STATES:
            problems.append(f"{rid}: invalid read_status")
        try:
            checked = date.fromisoformat(source.get("checked_at", ""))
            published = source.get("published_at")
            if published and date.fromisoformat(published) > checked:
                problems.append(f"{rid}: publication after checked_at")
        except ValueError:
            problems.append(f"{rid}: ISO date required (unknown publication is null)")
        for tid in source.get("topic_ids", []):
            if tid not in maps["topics"]:
                problems.append(f"{rid}: unknown topic {tid}")
    for rid, claim in maps["claims"].items():
        if claim.get("kind") not in KINDS:
            problems.append(f"{rid}: invalid claim kind")
        if not claim.get("text") or not claim.get("limitations"):
            problems.append(f"{rid}: text and limitations required")
        if claim.get("status") not in {"active", "superseded", "withdrawn", "needs_review"}:
            problems.append(f"{rid}: invalid status")
        if claim.get("kind") != "unknown" and not claim.get("source_ids"):
            problems.append(f"{rid}: provenance required")
        for sid in claim.get("source_ids", []):
            if sid not in maps["sources"]:
                problems.append(f"{rid}: unknown source {sid}")
            elif maps["sources"][sid].get("read_status") in {"metadata_only", "unread"} and claim.get("kind") in {"fact", "institution_statement"}:
                problems.append(f"{rid}: unread source cannot support a substantive fact")
        for tid in claim.get("topic_ids", []):
            if tid not in maps["topics"]:
                problems.append(f"{rid}: unknown topic {tid}")
        if claim.get("kind") == "hypothesis" and (not claim.get("alternative") or not claim.get("next_observation")):
            problems.append(f"{rid}: hypothesis needs alternative and next observation")
    return problems


def assert_valid(data):
    problems = errors(data)
    if problems:
        raise ValueError("\n".join(problems))


def graph(data):
    nodes, edges = [], []
    for source in data["sources"]:
        nodes.append({"id": source["id"], "type": "source", "label": source["title"]})
        for tid in source.get("topic_ids", []):
            edges.append({"from": source["id"], "to": tid, "type": "covers"})
    for claim in data["claims"]:
        nodes.append({"id": claim["id"], "type": "claim", "kind": claim["kind"], "status": claim["status"], "label": claim["text"]})
        for sid in claim.get("source_ids", []):
            edges.append({"from": sid, "to": claim["id"], "type": "grounds", "note": "provenance, not proof of causation"})
        for tid in claim.get("topic_ids", []):
            edges.append({"from": claim["id"], "to": tid, "type": "about"})
    for topic in data["topics"]:
        nodes.append({"id": topic["id"], "type": "topic", "label": topic["name"]})
    return {"semantics": "Edges are curated provenance/topic links, not estimated causality.", "nodes": nodes, "edges": edges}


def as_text(value):
    return "\n".join("- " + str(x) for x in value) if isinstance(value, list) else str(value)


def write_md(path, text):
    _atomic_write(path, _text_bytes(text.rstrip() + "\n"))


def build(root=ROOT):
    with writer_lock(root):
        _require_ready(root)
        data = _load_unlocked(Path(root))
        assert_valid(data)
        for relative, raw in _render(data).items():
            _atomic_write(Path(root) / relative, raw)
        return _counts(data)


def _counts(data):
    return {key: len(data[key]) for key in CORE_KEYS}


def _render(data):
    """Freeze generated bytes before the first transaction target is written."""
    assert_valid(data)
    output = {}
    root = Path()

    def write_md(path, text):
        output[path.as_posix()] = _text_bytes(text.rstrip() + "\n")

    def write_json(path, value):
        output[path.as_posix()] = _json_bytes(value)

    source_lines = ["# 읽은 자료와 활용 기록", "", "검색 발견·선택 절 읽기·전문 읽기를 구분한다. 공식 발표는 실현된 성과와 다르다. 원문 전문을 재배포하지 않고 링크와 자체 요약을 기록한다.", "", "| 자료 | 발행일 | 읽은 범위 | 확인일 |", "|---|---|---|---|"]
    for s in data["sources"]:
        source_lines.append(f"| [{s['id']} · {s['title']}](cards/{s['id']}.md) | {s.get('published_at') or '미확인/동적'} | {s['read_status']} | {s['checked_at']} |")
        claims = [c for c in data["claims"] if s["id"] in c.get("source_ids", [])]
        sections = [f"# {s['id']} · {s['title']}", f"[원문]({s['url']}) · {s['publisher']}", f"발행일: {s.get('published_at') or '미확인/동적'} · 확인일: {s['checked_at']}", f"읽기 상태: **{s['read_status']}**\n\n읽은 위치: {as_text(s['read_scope'])}", "## 자료의 핵심 내용\n\n" + as_text(s["summary"]), "## 이번 연구에 활용한 내용\n\n" + as_text(s["used_for"]), "## 해석의 한계\n\n" + as_text(s["limitations"]), "## 연결된 주장\n\n" + ("\n".join(f"- **{c['id']} / {c['kind']} / {c['status']}**: {c['text']}" for c in claims) or "아직 연결된 주장이 없음"), "[전체 자료 목록](../README.md)"]
        write_md(root / "sources" / "cards" / f"{s['id']}.md", "\n\n".join(sections))
    write_md(root / "sources" / "README.md", "\n".join(source_lines))
    wiki_index = ["# 주제별 연구 지도", "", "원장은 data/*.json이다. 이 페이지는 재생성되므로 수정은 원장과 reports/의 해석 문서에 남긴다.", ""]
    for topic in data["topics"]:
        tid = topic["id"]
        wiki_index.append(f"- [{topic['name']}]({tid}.md): {topic['question']}")
        relevant = [c for c in data["claims"] if tid in c.get("topic_ids", [])]
        lines = [f"# {topic['name']}", "", topic["question"], "", "## 현재 주장과 가설", ""]
        for c in relevant:
            links = ", ".join(f"[{sid}](../sources/cards/{sid}.md)" for sid in c.get("source_ids", []))
            lines.extend([f"### {c['id']} · {c['kind']} · {c['status']}", "", c["text"], "", f"근거: {links or '미확인'}", "", "한계: " + as_text(c["limitations"]), ""])
            for key, label in [("alternative", "다른 설명"), ("next_observation", "다음 관측")]:
                if c.get(key):
                    lines.extend([label + ": " + as_text(c[key]), ""])
        lines.extend(["## 관련 원문", ""] + [f"- [{s['id']} · {s['title']}](../sources/cards/{s['id']}.md)" for s in data["sources"] if tid in s.get("topic_ids", [])])
        lines.extend(["", "[전체 주제 지도](INDEX.md)"])
        write_md(root / "wiki" / f"{tid}.md", "\n".join(lines))
    write_md(root / "wiki" / "INDEX.md", "\n".join(wiki_index))
    write_json(root / "data" / "graph.json", graph(data))
    return output


def search(data, query, mode="lexical", limit=5):
    # Transparent baseline: case-insensitive word/substring matches, no LLM or embeddings.
    terms = set(re.findall(r"[\w-]+", query.lower()))
    ranked = []
    for source in data["sources"]:
        text = " ".join(str(source.get(k, "")) for k in ("title", "summary", "used_for", "topic_ids")).lower()
        score = sum(text.count(term) for term in terms)
        if score:
            ranked.append({"id": source["id"], "score": score, "via": "lexical", "url": source["url"]})
    ranked.sort(key=lambda x: (-x["score"], x["id"]))
    if mode == "graph" and ranked:
        # Return direct hits first; append related evidence through shared claim links.
        seeds = {r["id"] for r in ranked[:limit]}
        neighbors = {sid for c in data["claims"] if seeds.intersection(c.get("source_ids", [])) for sid in c.get("source_ids", [])} - {r["id"] for r in ranked}
        urls = {s["id"]: s["url"] for s in data["sources"]}
        ranked.extend({"id": sid, "score": 0, "via": "shared_claim", "url": urls[sid]} for sid in sorted(neighbors))
    return ranked[:limit]


def _merge(before, batch):
    if not isinstance(batch, dict) or not batch.get("change_reason"):
        raise ValueError("change_reason is required")
    after = {k: list(v) for k, v in before.items()}
    for kind in CORE_KEYS:
        if not isinstance(batch.get(kind, []), list):
            raise ValueError(f"{kind}: batch list required")
        existing = {r["id"]: r for r in before[kind]}
        seen = set()
        for record in batch.get(kind, []):
            if not isinstance(record, dict):
                raise ValueError(f"{kind}: batch record must be an object")
            rid = record.get("id")
            if rid in seen:
                raise ValueError(f"duplicate batch ID: {rid}")
            seen.add(rid)
            existing[rid] = record
        after[kind] = list(existing.values())
    assert_valid(after)  # Nothing is written before the complete proposed state passes.
    return after


def _snapshot(raw):
    return None if raw is None else {"sha256": _digest(raw), "base64": base64.b64encode(raw).decode("ascii")}


def _unpack(snapshot):
    if snapshot is None:
        return None
    raw = base64.b64decode(snapshot["base64"], validate=True)
    if _digest(raw) != snapshot["sha256"]:
        raise ValueError("Snapshot checksum mismatch")
    return raw


def _target(root, relative):
    # Frozen journals must never write outside their own checkout.
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or "\\" in relative or ":" in relative:
        raise ValueError(f"Unsafe transaction target: {relative}")
    result = Path(root) / path
    if not result.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError(f"Transaction target escapes repository: {relative}")
    return result


def _existing(path):
    return path.read_bytes() if path.exists() else None


def _journals(root):
    records = []
    for path in sorted((Path(root) / "history" / "transactions").glob("*.json")):
        try:
            envelope = read_json(path)
            payload = envelope["payload"]
            if envelope["sha256"] != _state_hash(payload) or payload["version"] != 1:
                raise ValueError("Journal checksum/version mismatch")
            raw_batch = _unpack(payload["batch"])
            if _digest(raw_batch) != payload["batch_sha256"]:
                raise ValueError("Frozen batch mismatch")
            for name in ("before", "after"):
                assert_valid(payload[name])
                if _state_hash(payload[name]) != payload[name + "_sha256"]:
                    raise ValueError(f"Journal {name} checksum mismatch")
            if _merge(payload["before"], json.loads(raw_batch.decode("utf-8-sig"))) != payload["after"]:
                raise ValueError("Journal batch does not produce its after-state")
            seen = set()
            for item in payload["targets"]:
                _target(root, item["path"])
                if item["path"] in seen:
                    raise ValueError("Duplicate transaction target")
                seen.add(item["path"])
                _unpack(item["before"])
                if _unpack(item["after"]) is None:
                    raise ValueError("Missing transaction after-snapshot")
            for kind in CORE_KEYS:
                item = next(t for t in payload["targets"] if t["path"] == f"data/{kind}.json")
                for name in ("before", "after"):
                    if json.loads(_unpack(item[name]).decode("utf-8-sig")) != payload[name][kind]:
                        raise ValueError("Core snapshot does not match validated state")
            done = path.with_suffix(".done")
            complete = done.exists()
            if complete and read_json(done) != {"journal_sha256": envelope["sha256"]}:
                raise ValueError("Completion marker checksum mismatch")
            records.append((path, envelope, complete))
        except (KeyError, TypeError, ValueError, StopIteration) as exc:
            raise ValueError(f"Invalid recovery journal {path.name}: {exc}") from exc
    return records


def has_pending(root=ROOT):
    """Advisory snapshot for runners; ingest rechecks under its OS writer lock."""
    return any(not complete for _, _, complete in _journals(root))


def _require_ready(root):
    if has_pending(root):
        raise ValueError("Incomplete research transaction; rerun ingest with the identical frozen batch before validate/build/search.")


def _check_expected(before_hash, after_hash, expected_before, expected_after):
    if expected_before is not None and before_hash not in {expected_before, expected_after}:
        raise ValueError("Stale plan: current/before state differs from the expected before/after state")
    if expected_after is not None and after_hash != expected_after:
        raise ValueError("Stale plan: proposed after-state differs from the expected after-state")


def _apply_journal(root, path, envelope):
    payload = envelope["payload"]
    # Check every target first. A conflict never triggers partial recovery writes.
    for item in payload["targets"]:
        current = _existing(_target(root, item["path"]))
        if current not in (_unpack(item["before"]), _unpack(item["after"])):
            raise ValueError(f"Recovery conflict: {item['path']} changed outside this transaction; nothing was overwritten")
    for item in payload["targets"]:
        target = _target(root, item["path"])
        wanted = _unpack(item["after"])
        if _existing(target) != wanted:
            _atomic_write(target, wanted)
    # Verify all output before acknowledging completion, including history.
    for item in payload["targets"]:
        if _existing(_target(root, item["path"])) != _unpack(item["after"]):
            raise ValueError(f"Transaction output changed during write: {item['path']}")
    write_json(path.with_suffix(".done"), {"journal_sha256": envelope["sha256"]})
    changed = payload["before_sha256"] != payload["after_sha256"]
    return {"status": "updated" if changed else "unchanged", **({"sha256": payload["after_sha256"]} if changed else {}), **_counts(payload["after"])}


def ingest(root, batch_path, *, expected_before_sha256=None, expected_after_sha256=None):
    """Resume only this exact batch, refusing conflicting edits or stale plans.

    Journals/complete markers are append-only. Local cooperative writers only;
    manual edits and cloud-sync writers must be paused during an invocation.
    """
    root = Path(root)
    with writer_lock(root):
        batch_raw = Path(batch_path).read_bytes()
        batch_hash = _digest(batch_raw)
        records = _journals(root)
        pending = [(p, e) for p, e, complete in records if not complete]
        if pending:
            if len(pending) != 1 or pending[0][1]["payload"]["batch_sha256"] != batch_hash:
                raise ValueError("Another batch has an incomplete transaction; resume its identical frozen batch first")
            path, envelope = pending[0]
            payload = envelope["payload"]
            _check_expected(payload["before_sha256"], payload["after_sha256"], expected_before_sha256, expected_after_sha256)
            return _apply_journal(root, path, envelope)

        before = _load_unlocked(root)
        assert_valid(before)
        batch = json.loads(batch_raw.decode("utf-8-sig"))
        after = _merge(before, batch)
        old_hash, new_hash = _state_hash(before), _state_hash(after)
        _check_expected(old_hash, new_hash, expected_before_sha256, expected_after_sha256)
        matching = [(p, e) for p, e, complete in records if complete and e["payload"]["batch_sha256"] == batch_hash]
        if matching:
            previous = matching[-1][1]["payload"]
            if old_hash != previous["after_sha256"]:
                raise ValueError("Completed batch is stale: later research or user edits changed the current state")
            for item in previous["targets"]:
                current = _existing(_target(root, item["path"]))
                # Missing generated files can be rebuilt in a new no-op journal.
                generated = item["path"] == "data/graph.json" or item["path"].startswith(("sources/", "wiki/"))
                if current != _unpack(item["after"]) and not (generated and current is None):
                    raise ValueError(f"Completed batch conflict: {item['path']} changed; nothing was overwritten")

        changed = old_hash != new_hash
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        outputs = {}
        if changed:
            history = {"recorded_at_utc": stamp, "change_reason": batch["change_reason"], "before_sha256": old_hash, "after_sha256": new_hash, "before": before, "after": after}
            outputs[f"history/{stamp}-{new_hash[:10]}.json"] = _json_bytes(history)
        for kind in CORE_KEYS:
            relative = f"data/{kind}.json"
            outputs[relative] = _json_bytes(after[kind]) if changed else (root / relative).read_bytes()
        outputs.update(_render(after))
        targets = [{"path": name, "before": _snapshot(_existing(_target(root, name))), "after": _snapshot(raw)} for name, raw in outputs.items()]
        empty_batch = not any(batch.get(kind) for kind in CORE_KEYS)
        if (matching or empty_batch) and not changed and all(t["before"] == t["after"] for t in targets):
            return {"status": "unchanged", **_counts(after)}
        # History names are unique; never replace an existing immutable record.
        if changed and targets[0]["before"] is not None:
            raise ValueError("History path already exists; retry without overwriting it")
        payload = {"version": 1, "batch_sha256": batch_hash, "batch": _snapshot(batch_raw), "before_sha256": old_hash, "after_sha256": new_hash, "before": before, "after": after, "targets": targets}
        envelope = {"sha256": _state_hash(payload), "payload": payload}
        path = root / "history" / "transactions" / f"{stamp}-{batch_hash[:16]}.json"
        if path.exists():
            raise ValueError("Recovery journal already exists; retry without overwriting it")
        write_json(path, envelope)  # First durable mutation, before any data/history/output.
        return _apply_journal(root, path, envelope)


def check_links(root):
    broken = []
    for path in root.rglob("*.md"):
        for target in re.findall(r"(?<!!)\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if target.startswith(("https://", "http://", "#", "mailto:")):
                continue
            target = unquote(target.strip("<>").split("#")[0])
            if target:
                resolved = (path.parent / target).resolve()
                if not resolved.is_relative_to(root.resolve()):
                    broken.append(f"{path.relative_to(root)} -> outside repository: {target}")
                elif not resolved.exists():
                    broken.append(f"{path.relative_to(root)} -> {target}")
    return broken


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    sub.add_parser("build")
    p = sub.add_parser("search")
    p.add_argument("query")
    p.add_argument("--mode", choices=("lexical", "graph"), default="lexical")
    p.add_argument("--limit", type=int, default=5)
    p = sub.add_parser("ingest")
    p.add_argument("batch", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "validate":
            with writer_lock(args.root):
                _require_ready(args.root)
                data = _load_unlocked(args.root)
                assert_valid(data)
                broken = check_links(args.root)
                if broken:
                    raise ValueError("Broken local links:\n" + "\n".join(broken))
                result = {"status": "valid", **_counts(data)}
        elif args.command == "build":
            result = build(args.root)
        elif args.command == "search":
            with writer_lock(args.root):
                _require_ready(args.root)
                data = _load_unlocked(args.root)
                assert_valid(data)
                result = search(data, args.query, args.mode, args.limit)
        else:
            result = ingest(args.root, args.batch)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
