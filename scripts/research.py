"""Source-backed research records, wiki generation and retrieval. Python 3.11+, stdlib only."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parents[1]
KINDS = {"fact", "institution_statement", "interpretation", "hypothesis", "unknown"}
READ_STATES = {"full_text", "selected_sections", "official_summary", "metadata_only", "unread"}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load(root=ROOT):
    return {key: read_json(root / "data" / f"{key}.json") for key in ("sources", "claims", "topics")}


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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def build(root=ROOT):
    data = load(root)
    assert_valid(data)
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
    return {"sources": len(data["sources"]), "claims": len(data["claims"]), "topics": len(data["topics"])}


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


def ingest(root, batch_path):
    before = load(root)
    batch = read_json(batch_path)
    if not batch.get("change_reason"):
        raise ValueError("change_reason is required")
    after = {k: list(v) for k, v in before.items()}
    for kind in ("sources", "claims", "topics"):
        existing = {r["id"]: r for r in before[kind]}
        seen = set()
        for record in batch.get(kind, []):
            rid = record.get("id")
            if rid in seen:
                raise ValueError(f"duplicate batch ID: {rid}")
            seen.add(rid)
            existing[rid] = record
        after[kind] = list(existing.values())
    assert_valid(after)  # Nothing is written before the complete proposed state passes.
    canonical = lambda x: json.dumps(x, sort_keys=True, ensure_ascii=False).encode()
    if canonical(before) == canonical(after):
        return {"status": "unchanged", **build(root)}  # Recover interrupted/missing generated files.
    old_hash = hashlib.sha256(canonical(before)).hexdigest()
    new_hash = hashlib.sha256(canonical(after)).hexdigest()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    history = {"recorded_at_utc": stamp, "change_reason": batch["change_reason"], "before_sha256": old_hash, "after_sha256": new_hash, "before": before, "after": after}
    write_json(root / "history" / f"{stamp}-{new_hash[:10]}.json", history)
    # Local single-writer workflow. Run in an isolated checkout; interruption requires validation/rebuild.
    for kind, records in after.items():
        write_json(root / "data" / f"{kind}.json", records)
    return {"status": "updated", "sha256": new_hash, **build(root)}


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
            data = load(args.root)
            assert_valid(data)
            broken = check_links(args.root)
            if broken:
                raise ValueError("Broken local links:\n" + "\n".join(broken))
            result = {"status": "valid", "sources": len(data["sources"]), "claims": len(data["claims"]), "topics": len(data["topics"])}
        elif args.command == "build":
            result = build(args.root)
        elif args.command == "search":
            data = load(args.root)
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
