#!/usr/bin/env python3
"""Read-only source -> claim -> hypothesis -> action contract checks.

Passing checks proves reference/metadata consistency, not the truth, adequacy,
causal meaning, freshness, or predictive quality of the research.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA_VERSION = "1.0"
READ_STATES = {"full_text", "selected_sections", "official_summary", "metadata_only", "unread"}
KINDS = {"fact", "institution_statement", "interpretation", "hypothesis", "unknown"}
BOUNDARY = "Structural and declared reading-metadata checks only; no semantic or forecast validation."


def digest(value: Any) -> str:
    """Stable hash of a referenced JSON value or Markdown section string."""
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _path(root: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or "\\" in name or ":" in name:
        raise ValueError("paths must be public repository-relative POSIX paths")
    rel = PurePosixPath(name)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("path escapes repository")
    target = (root / name).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError("resolved path escapes repository")
    return target


def _manifest(root: Path, manifest: str | Path | dict) -> dict:
    if isinstance(manifest, dict):
        return manifest
    p = Path(manifest)
    p = p if p.is_absolute() else root / p
    if not p.resolve().is_relative_to(root.resolve()):
        raise ValueError("manifest must be inside repository")
    value = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("manifest must be an object")
    return value


def pointer(value: Any, ptr: str) -> Any:
    if not isinstance(ptr, str) or (ptr and not ptr.startswith("/")):
        raise ValueError("invalid JSON pointer")
    for part in ptr.split("/")[1:] if ptr else []:
        if "~" in part.replace("~0", "").replace("~1", ""):
            raise ValueError("invalid JSON pointer escape")
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            if not part.isascii() or not part.isdigit() or (len(part) > 1 and part.startswith("0")):
                raise ValueError("invalid JSON array index")
            value = value[int(part)]
        else:
            value = value[part]
    return value


def markdown_section(text: str, heading: str) -> str:
    """Exact unique ATX heading through the next same/higher-level heading."""
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if line == heading]
    if len(starts) != 1 or not heading.startswith("#") or " " not in heading:
        raise ValueError("Markdown heading must match exactly once")
    level = len(heading) - len(heading.lstrip("#"))
    end = len(lines)
    for i in range(starts[0] + 1, len(lines)):
        line = lines[i]
        n = len(line) - len(line.lstrip("#"))
        if 0 < n <= level and line[n:n + 1] == " ":
            end = i
            break
    return "\n".join(lines[starts[0]:end]).rstrip()


def input_paths(root: str | Path, manifest: str | Path | dict) -> list[Path]:
    """All referenced input files, plus the manifest when given as a path."""
    root = Path(root).resolve()
    spec = _manifest(root, manifest)
    found: set[Path] = set()
    if not isinstance(manifest, dict):
        p = Path(manifest)
        found.add((p if p.is_absolute() else root / p).resolve())

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if "path" in value:
                found.add(_path(root, value["path"]))
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(spec)
    return sorted(found)


class _Check:
    def __init__(self, root: Path, spec: dict, data: dict | None):
        self.root, self.spec, self.data = root, spec, data
        self.problems: list[str] = []
        self.cache: dict[str, Any] = {}
        self.sources: dict[str, dict] = {}
        self.claims: dict[str, dict] = {}
        self.counts: dict[str, int] = {}
        self.effective_states: dict[str, list[str]] = {}

    def fail(self, code: str, where: str, message: str) -> None:
        self.problems.append(f"{code} {where}: {message}")

    def read(self, name: str) -> Any:
        target = _path(self.root, name)
        if name not in self.cache:
            self.cache[name] = json.loads(target.read_text(encoding="utf-8"))
        return self.cache[name]

    def ref(self, ref: Any, where: str) -> Any:
        if not isinstance(ref, dict):
            self.fail("REF", where, "reference must be an object")
            return None
        try:
            if ref.get("format", "json") == "markdown_section":
                value = markdown_section(_path(self.root, ref["path"]).read_text(encoding="utf-8"), ref["heading"])
            elif ref.get("format", "json") == "json":
                value = pointer(self.read(ref["path"]), ref["pointer"])
            else:
                raise ValueError("unknown reference format")
            if "expected_id" in ref and (not isinstance(value, dict) or value.get("id") != ref["expected_id"]):
                self.fail("REF_ID", where, "record ID differs from the declared original")
            if not isinstance(ref.get("sha256"), str) or digest(value) != ref["sha256"]:
                self.fail("REF_HASH", where, "referenced value changed or hash missing; review impact explicitly")
            return value
        except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
            self.fail("REF", where, f"cannot resolve reference ({type(exc).__name__})")
            return None

    def ids(self, value: Any, where: str, allow_empty: bool = False) -> list[str]:
        if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
            self.fail("TYPE", where, "expected a list of nonempty identifiers")
            return []
        if len(value) != len(set(value)):
            self.fail("DUPLICATE", where, "duplicate identifier")
        if not value and not allow_empty:
            self.fail("EMPTY", where, "at least one identifier is required")
        return value

    def records(self, key: str) -> list[dict]:
        values = self.spec.get(key)
        if not isinstance(values, list) or any(not isinstance(x, dict) for x in values):
            self.fail("TYPE", key, "expected an array of objects")
            return []
        self.ids([x.get("id") for x in values], key)
        self.counts[key] = len(values)
        return values

    def known_sources(self, ids: list[str], where: str) -> None:
        for sid in ids:
            if sid not in self.sources:
                self.fail("UNKNOWN_SOURCE", where, sid)

    def registry(self, key: str) -> dict[str, dict]:
        name = self.spec["registries"][key]["path"]
        _path(self.root, name)
        value = self.data[key] if self.data is not None and key in self.data else self.read(name)
        # All JSON references to a registry use the proposed data during a dry run.
        self.cache[name] = value
        if not isinstance(value, list) or any(not isinstance(x, dict) for x in value):
            raise ValueError(f"{key} registry must contain objects")
        ids = self.ids([x.get("id") for x in value], key)
        return dict(zip(ids, value))

    @staticmethod
    def child_ref(child: dict, parent: dict) -> bool:
        return (child.get("path") == parent.get("path") and
                child.get("pointer", "").startswith(parent.get("pointer", "") + "/"))

    def check_events(self) -> None:
        events_ref = self.spec["read_events"]
        events = self.ref(events_ref, "read_events")
        if not isinstance(events, list) or any(not isinstance(x, dict) for x in events):
            self.fail("TYPE", "read_events", "expected array of events")
            return
        self.counts["read_events"] = len(events)
        if len({digest(event) for event in events}) != len(events):
            self.fail("DUPLICATE", "read_events", "identical read event occurs more than once")
        if len(events) != events_ref.get("expected_count"):
            self.fail("EVENT_COUNT", "read_events", "immutable event count differs")
        fixes = self.spec.get("read_status_corrections", [])
        if not isinstance(fixes, list) or any(not isinstance(x, dict) for x in fixes):
            self.fail("TYPE", "read_status_corrections", "expected array")
            fixes = []
        by_index: dict[int, dict] = {}
        for i, fix in enumerate(fixes):
            loc = f"read_status_corrections/{i}"
            index = fix.get("event_index")
            if type(index) is not int or index < 0 or index >= len(events):
                self.fail("CORRECTION_EVENT", loc, "invalid event index")
                continue
            if index in by_index:
                self.fail("DUPLICATE", loc, "event corrected twice")
            by_index[index] = fix
            event = events[index]
            ref = fix.get("event_ref", {})
            resolved = self.ref(ref, loc + "/event_ref")
            if (ref.get("path") != events_ref["path"] or
                    ref.get("pointer") != events_ref["pointer"] + f"/{index}" or resolved != event):
                self.fail("CORRECTION_EVENT", loc, "correction must reference its exact original event")
            if (event.get("source_id") != fix.get("source_id") or "read_status" not in event or event["read_status"] is not None or
                    fix.get("original_read_status", "missing") is not None or fix.get("corrected_read_status") != "selected_sections"):
                self.fail("CORRECTION_PRECONDITION", loc, "only explicit null -> selected_sections metadata repair is supported")
            if fix.get("new_read_performed") is not False or not isinstance(fix.get("reason"), str) or not fix["reason"].strip():
                self.fail("CORRECTION_REASON", loc, "must state existing metadata basis and no new read")
            scope_ref = fix.get("source_scope_ref", {})
            scope = self.ref(scope_ref, loc + "/source_scope_ref")
            source_ref = fix.get("source_ref", {})
            source = self.ref(source_ref, loc + "/source_ref")
            if (not isinstance(source, dict) or source.get("id") != fix.get("source_id") or
                    source_ref.get("path") != self.spec["registries"]["sources"]["path"] or
                    not self.child_ref(scope_ref, source_ref) or
                    not scope_ref.get("pointer", "").startswith(source_ref.get("pointer", "") + "/read_scope/") or
                    not isinstance(scope, str) or not scope.strip() or scope != event.get("read_scope")):
                self.fail("CORRECTION_BASIS", loc, "event scope must exactly match the identified registry source scope")
        self.counts["read_status_corrections"] = len(fixes)
        for i, event in enumerate(events):
            sid = event.get("source_id")
            if sid not in self.sources:
                self.fail("UNKNOWN_SOURCE", f"read_events/{i}", str(sid))
            state = by_index.get(i, {}).get("corrected_read_status", event.get("read_status"))
            if state not in READ_STATES:
                self.fail("READ_STATUS", f"read_events/{i}", "missing or invalid read_status; original event is not changed")
            self.effective_states.setdefault(sid, []).append(state)

    def check(self) -> None:
        if self.spec.get("schema_version") != SCHEMA_VERSION:
            self.fail("VERSION", "schema_version", "unsupported schema version")
        if not isinstance(self.spec.get("run_id"), str) or not self.spec["run_id"].strip():
            self.fail("TYPE", "run_id", "nonempty run ID required")
        self.sources, self.claims = self.registry("sources"), self.registry("claims")
        self.check_events()
        scope = self.spec.get("scope", {})
        manifests = {k: self.records(k) for k in ("claims", "hypotheses", "actions")}
        for key, items in manifests.items():
            expected = self.ids(scope.get(key), f"scope/{key}")
            actual = [x.get("id") for x in items]
            if set(expected) != set(actual):
                self.fail("SCOPE", key, "missing or unexpected scoped records")
        run_claim_ids = {cid for cid, claim in self.claims.items() if claim.get("run") == self.spec["run_id"]}
        if run_claim_ids != {claim.get("id") for claim in manifests["claims"]}:
            self.fail("RUN_CLAIM_SCOPE", "claims", "manifest must include every claim assigned to this run")
        claims_by_id: dict[str, dict] = {}
        for claim in manifests["claims"]:
            cid, loc = claim["id"], "claims/" + claim["id"]
            ref = claim.get("ref", {})
            original = self.ref(ref, loc)
            if (ref.get("path") != self.spec["registries"]["claims"]["path"] or
                    not isinstance(original, dict) or original.get("id") != cid):
                self.fail("CLAIM_REF", loc, "must refer to the same ID in the claim registry")
                continue
            claims_by_id[cid] = original
            if original.get("kind") not in KINDS or original.get("kind") != claim.get("kind"):
                self.fail("CLAIM_KIND", loc, "invalid kind or kind differs from declared type")
            if original.get("run") != self.spec["run_id"]:
                self.fail("CLAIM_RUN", loc, "claim does not belong to this run")
            if original.get("status") != "active":
                self.fail("CLAIM_STATUS", loc, "current-run lineage requires an active claim; review replacement explicitly")
            sids = self.ids(claim.get("source_ids"), loc + "/source_ids", original.get("kind") == "unknown")
            actual_sids = self.ids(original.get("source_ids"), loc + "/original_source_ids", original.get("kind") == "unknown")
            if set(sids) != set(actual_sids):
                self.fail("SOURCE_MISMATCH", loc, "declared sources differ from original claim")
            self.known_sources(sids, loc)
            for sid in sids:
                state = self.sources.get(sid, {}).get("read_status")
                if state not in READ_STATES:
                    self.fail("READ_STATUS", loc, f"{sid} has invalid registry read status")
                if original.get("kind") in {"fact", "institution_statement"}:
                    states = [state] + self.effective_states.get(sid, [])
                    if any(x in {"metadata_only", "unread", None} for x in states):
                        self.fail("UNREAD_FACT", loc, f"{sid}: insufficient declared reading state for factual use")
            if original.get("kind") == "hypothesis":
                for field in ("alternative", "next_observation"):
                    if not isinstance(original.get(field), str) or not original[field].strip():
                        self.fail("HYPOTHESIS_FIELD", loc, f"missing {field}")

        used_source_ids = {sid for c in claims_by_id.values() for sid in c.get("source_ids", [])}
        context_ids = self.ids(self.spec.get("context_only_read_source_ids"), "context_only_read_source_ids", True)
        self.known_sources(context_ids, "context_only_read_source_ids")
        if set(context_ids) != set(self.effective_states) - used_source_ids:
            self.fail("CONTEXT_SOURCE", "read_events", "unlinked readings must be explicitly classified as context only")
        self.counts["claim_sources"] = len(used_source_ids)
        self.counts["context_only_read_sources"] = len(context_ids)

        hyp_ids = {x["id"] for x in manifests["hypotheses"]}
        used_claims: set[str] = set()
        hyp_claims: dict[str, set[str]] = {}
        for hyp in manifests["hypotheses"]:
            hid, loc = hyp["id"], "hypotheses/" + hyp["id"]
            opening = self.ref(hyp.get("opening_ref"), loc + "/opening")
            closing_ref = hyp.get("closing_ref", {})
            closing = self.ref(closing_ref, loc + "/closing")
            if any(not isinstance(x, dict) or x.get("id") != hid for x in (opening, closing)):
                self.fail("HYPOTHESIS_REF", loc, "opening and closing must preserve the same hypothesis ID")
            closing_sources = self.ref(hyp.get("closing_sources_ref"), loc + "/closing_sources")
            closing_sids = self.ids(closing_sources, loc + "/closing_source_ids")
            self.known_sources(closing_sids, loc)
            for field in ("alternative_ref", "next_observations_ref", "closing_sources_ref"):
                ref = hyp.get(field, {})
                value = self.ref(ref, loc + "/" + field)
                original_field = {"alternative_ref": "strongest_alternative", "next_observations_ref": "next_observations",
                                  "closing_sources_ref": "source_ids"}[field]
                if (ref.get("path") != closing_ref.get("path") or
                        ref.get("pointer") != closing_ref.get("pointer", "") + "/" + original_field):
                    self.fail("HYPOTHESIS_FIELD", loc, f"{field} must reference this closing hypothesis's {original_field}")
                if field == "alternative_ref" and (not isinstance(value, str) or not value.strip()):
                    self.fail("ALTERNATIVE", loc, "strongest alternative must be nonempty text")
                if field == "next_observations_ref" and (not isinstance(value, list) or not value or any(not isinstance(x, str) or not x.strip() for x in value)):
                    self.fail("NEXT_OBSERVATION", loc, "discriminating next observations must be a nonempty text list")
            links = hyp.get("claim_links")
            if not isinstance(links, list) or not links or any(not isinstance(x, dict) for x in links):
                self.fail("TYPE", loc, "claim_links must be a nonempty object list")
                continue
            ids = self.ids([x.get("claim_id") for x in links], loc + "/claim_links")
            hyp_claims[hid] = set(ids)
            for link in links:
                cid = link.get("claim_id")
                used_claims.add(cid)
                original = claims_by_id.get(cid)
                if original is None:
                    self.fail("UNKNOWN_CLAIM", loc, str(cid))
                    continue
                sids = self.ids(link.get("source_ids"), loc + f"/{cid}/source_ids")
                shared = self.ids(link.get("shared_closing_source_ids"), loc + f"/{cid}/shared_sources")
                if set(sids) != set(original.get("source_ids", [])) or set(shared) != set(sids).intersection(closing_sids):
                    self.fail("SOURCE_MISMATCH", loc, f"{cid}: edge sources/shared original citations differ")
        if set(claims_by_id) - used_claims:
            self.fail("ORPHAN_CLAIM", "claims", ",".join(sorted(set(claims_by_id) - used_claims)))

        group_refs = self.spec.get("groups", {})
        if not isinstance(group_refs, dict):
            raise ValueError("groups must map group IDs to original JSON references")
        groups = {key: self.ref(ref, "groups/" + key) for key, ref in group_refs.items()}
        action_refs: set[tuple] = set()
        used_hypotheses: set[str] = set()
        for action in manifests["actions"]:
            loc = "actions/" + action["id"]
            ref = action.get("ref", {})
            value = self.ref(ref, loc)
            if not isinstance(value, str) or not value.strip():
                self.fail("ACTION_REF", loc, "action must reference nonempty original action text/section")
            ref_key = (ref.get("path"), ref.get("pointer"), ref.get("heading"))
            if ref_key in action_refs:
                self.fail("DUPLICATE", loc, "same original action referenced twice")
            action_refs.add(ref_key)
            group = action.get("group")
            group_ref = group_refs.get(group, {})
            group_record = groups.get(group)
            if not isinstance(group_record, dict):
                self.fail("ACTION_GROUP", loc, "unknown group")
            elif ref.get("format") == "markdown_section":
                if ref.get("path") != group_record.get("report"):
                    self.fail("ACTION_GROUP", loc, "section must belong to the group's original report")
            elif (not self.child_ref(ref, group_ref) or
                  not ref.get("pointer", "").startswith(group_ref.get("pointer", "") + "/priorities/")):
                self.fail("ACTION_GROUP", loc, "JSON action must belong to this group's original priorities")
            decisions = action.get("decision_refs", [])
            if not isinstance(decisions, list) or not decisions:
                self.fail("ACTION_DECISION", loc, "original group decision references are required")
                decisions = []
            for decision_ref in decisions:
                decision = self.ref(decision_ref, loc + "/decision")
                if not isinstance(decision, dict) or not decision.get("id") or not self.child_ref(decision_ref, group_ref):
                    self.fail("ACTION_DECISION", loc, "decision must have an original ID and belong to this group")
            aids = self.ids(action.get("hypothesis_ids"), loc + "/hypothesis_ids")
            cids = self.ids(action.get("claim_ids"), loc + "/claim_ids")
            for hid in aids:
                if hid not in hyp_ids:
                    self.fail("UNKNOWN_HYPOTHESIS", loc, hid)
                elif not set(cids).intersection(hyp_claims.get(hid, set())):
                    self.fail("ACTION_HYPOTHESIS", loc, f"{hid} has no shared claim with this action")
                used_hypotheses.add(hid)
            allowed = set().union(*(hyp_claims.get(hid, set()) for hid in aids))
            for cid in cids:
                if cid not in allowed:
                    self.fail("ACTION_CLAIM", loc, f"{cid} is not connected through this action's hypotheses")
        if hyp_ids - used_hypotheses:
            self.fail("ORPHAN_HYPOTHESIS", "hypotheses", ",".join(sorted(hyp_ids - used_hypotheses)))


def _run(root: str | Path, manifest: str | Path | dict, data: dict | None) -> _Check:
    root = Path(root).resolve()
    check = _Check(root, {}, data)
    try:
        check.spec = _manifest(root, manifest)
        # Validate every declared path even if a malformed object is otherwise skipped.
        input_paths(root, check.spec)
        check.check()
    except (OSError, ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
        check.fail("MANIFEST", "root", f"malformed/unreadable input ({type(exc).__name__}: {exc})")
    return check


def errors(root: str | Path, manifest: str | Path | dict, data: dict | None = None) -> list[str]:
    """Collect errors; optional proposed registries never replace immutable run inputs."""
    return _run(root, manifest, data).problems


def validate(root: str | Path, manifest: str | Path | dict, data_override: dict | None = None) -> dict:
    """Return a summary or raise ValueError. No reads are performed on the network; no writes."""
    check = _run(root, manifest, data_override)
    if check.problems:
        raise ValueError("\n".join(check.problems))
    return {"valid": True, "schema_version": SCHEMA_VERSION, "run_id": check.spec["run_id"],
            "counts": check.counts, "validation_boundary": BOUNDARY}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    try:
        summary = validate(args.root, args.manifest)
    except ValueError as exc:
        print(json.dumps({"valid": False, "errors": str(exc).splitlines(), "validation_boundary": BOUNDARY}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
