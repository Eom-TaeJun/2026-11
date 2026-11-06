import copy
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MANIFEST = "data/research_lineage_20261106.json"
HISTORICAL_STATE = "history/20261106T144500115564Z-a156cfc195.json"


def _module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lineage = _module("lineage_under_test", REPO / "scripts/lineage.py")
research = _module("research_for_lineage_test", REPO / "scripts/research.py")


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_fixture(root):
    """Small synthetic, research+lineage-valid fixture for pipeline integration tests.

    Writes only below the caller's temporary root; returns the relative manifest path.
    """
    root = Path(root)
    data = {
        "sources": [{"id": "SRC-1", "title": "Redemption", "publisher": "Example",
                     "url": "https://example.org/report", "visibility": "public",
                     "checked_at": "2026-11-06", "published_at": None,
                     "read_status": "selected_sections", "read_scope": ["section 2"],
                     "summary": "Redemption cash", "used_for": "Liquidity question",
                     "limitations": "No measured outcome", "topic_ids": ["T-CASH"]}],
        "claims": [{"id": "C-1", "kind": "hypothesis", "status": "active",
                    "run": "fixture-run", "text": "Cash conditions matter",
                    "source_ids": ["SRC-1"], "topic_ids": ["T-CASH"], "limitations": "Conditional",
                    "alternative": "Existing rail", "next_observation": "Bank receipt"}],
        "topics": [{"id": "T-CASH", "name": "Cash", "question": "When is cash available?"}],
    }
    for key, value in data.items():
        write_json(root / "data" / f"{key}.json", value)
    write_json(root / "runs/events.json", {"read_events": [
        {"source_id": "SRC-1", "read_status": "selected_sections", "read_scope": "section 2"}]})
    write_json(root / "runs/opening.json", {"hypotheses": [{"id": "OPEN-1", "initial_stance": "Conditional"}]})
    write_json(root / "data/outlook.json", {
        "closing": {"judgments": [{"id": "OPEN-1", "source_ids": ["SRC-1"],
                                   "strongest_alternative": "Existing rail wins", "next_observations": ["Receipt time"]}]},
        "groups": {"example": {"priorities": ["Check actual receipt"],
                                "decisions": [{"id": "DEC-1", "updated": "Compare alternatives"}]}}})

    def ref(path, pointer, ident=None):
        value = lineage.pointer(json.loads((root / path).read_text(encoding="utf-8")), pointer)
        result = {"path": path, "pointer": pointer, "sha256": lineage.digest(value)}
        if ident:
            result["expected_id"] = ident
        return result

    closing = "/closing/judgments/0"
    manifest = {
        "schema_version": "1.0", "run_id": "fixture-run",
        "registries": {"sources": {"path": "data/sources.json"}, "claims": {"path": "data/claims.json"}},
        "read_events": dict(ref("runs/events.json", "/read_events"), expected_count=1),
        "read_status_corrections": [], "context_only_read_source_ids": [],
        "scope": {"claims": ["C-1"], "hypotheses": ["OPEN-1"], "actions": ["A-1"]},
        "claims": [{"id": "C-1", "ref": ref("data/claims.json", "/0", "C-1"),
                    "kind": "hypothesis", "source_ids": ["SRC-1"]}],
        "hypotheses": [{"id": "OPEN-1", "opening_ref": ref("runs/opening.json", "/hypotheses/0", "OPEN-1"),
                        "closing_ref": ref("data/outlook.json", closing, "OPEN-1"),
                        "closing_sources_ref": ref("data/outlook.json", closing + "/source_ids"),
                        "alternative_ref": ref("data/outlook.json", closing + "/strongest_alternative"),
                        "next_observations_ref": ref("data/outlook.json", closing + "/next_observations"),
                        "claim_links": [{"claim_id": "C-1", "source_ids": ["SRC-1"],
                                         "shared_closing_source_ids": ["SRC-1"]}]}],
        "groups": {"example": ref("data/outlook.json", "/groups/example")},
        "actions": [{"id": "A-1", "group": "example",
                     "ref": ref("data/outlook.json", "/groups/example/priorities/0"),
                     "decision_refs": [ref("data/outlook.json", "/groups/example/decisions/0", "DEC-1")],
                     "hypothesis_ids": ["OPEN-1"], "claim_ids": ["C-1"]}],
    }
    name = "data/lineage_fixture.json"
    write_json(root / name, manifest)
    return name


class LineageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for path in lineage.input_paths(REPO, MANIFEST):
            target = self.root / path.relative_to(REPO)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        # This manifest describes the November 6 run. A later legitimate source
        # recheck changes the live registry and must not silently rehash history.
        snapshot = json.loads((REPO / HISTORICAL_STATE).read_text(encoding="utf-8"))
        self.assertEqual(research._state_hash(snapshot["after"]), snapshot["after_sha256"])
        for key in ("sources", "claims"):
            write_json(self.root / "data" / f"{key}.json", snapshot["after"][key])
        self.manifest = json.loads((self.root / MANIFEST).read_text(encoding="utf-8"))

    def problems(self):
        return lineage.errors(self.root, self.manifest)

    def assertCode(self, code):
        found = self.problems()
        self.assertTrue(any(x.startswith(code + " ") for x in found), found)

    def change_json(self, path, pointer, value):
        doc = json.loads((self.root / path).read_text(encoding="utf-8"))
        parent_ptr, _, key = pointer.rpartition("/")
        parent = lineage.pointer(doc, parent_ptr)
        parent[int(key) if isinstance(parent, list) else key] = value
        write_json(self.root / path, doc)

    def rehash(self):
        """Simulate an explicit manifest update; structural errors must still fail."""
        def walk(value):
            if isinstance(value, dict):
                if "path" in value and "pointer" in value:
                    document = json.loads((self.root / value["path"]).read_text(encoding="utf-8"))
                    value["sha256"] = lineage.digest(lineage.pointer(document, value["pointer"]))
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
        walk(self.manifest)

    def test_historical_manifest_passes_without_mutation(self):
        before = {p: p.read_bytes() for p in lineage.input_paths(self.root, MANIFEST)}
        result = lineage.validate(self.root, self.manifest)
        self.assertEqual(result["counts"]["read_events"], 33)
        self.assertEqual(result["counts"]["read_status_corrections"], 5)
        self.assertEqual(result["counts"]["claims"], 12)
        self.assertEqual(result["counts"]["hypotheses"], 6)
        self.assertEqual(result["counts"]["actions"], 9)
        self.assertEqual(result["counts"]["claim_sources"], 28)
        self.assertEqual(result["counts"]["context_only_read_sources"], 5)
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_later_source_recheck_does_not_rewrite_historical_evidence(self):
        fix = self.manifest["read_status_corrections"][2]
        source_ref = fix["source_ref"]
        source_path = self.root / source_ref["path"]
        original = source_path.read_bytes()
        sources = json.loads(original)
        source = lineage.pointer(sources, source_ref["pointer"])
        source["checked_at"] = "2026-11-07"
        source["read_scope"].append("Later selected reading; original event unchanged")
        write_json(source_path, sources)
        self.assertCode("REF_HASH")
        source_path.write_bytes(original)
        self.assertTrue(lineage.validate(self.root, self.manifest)["valid"])

    def test_prior_registry_validator_misses_exactly_five_null_event_states(self):
        data = {key: json.loads((REPO / "data" / f"{key}.json").read_text(encoding="utf-8"))
                for key in ("sources", "claims", "topics")}
        self.assertEqual(research.errors(data), [])
        self.manifest["read_status_corrections"] = []
        found = [x for x in self.problems() if x.startswith("READ_STATUS read_events/")]
        self.assertEqual(len(found), 5, found)
        self.assertEqual([x.split(":")[0] for x in found], [f"READ_STATUS read_events/{i}" for i in range(5)])

    def test_synthetic_fixture_works_for_a_different_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = make_fixture(root)
            self.assertEqual(research.errors(research.load(root)), [])
            self.assertTrue(lineage.validate(root, manifest)["valid"])

    def test_unknown_source(self):
        self.manifest["claims"][0]["source_ids"].append("SOURCE-MISSING")
        self.assertCode("UNKNOWN_SOURCE")

    def test_wrong_claim_kind(self):
        self.manifest["claims"][0]["kind"] = "fact"
        self.assertCode("CLAIM_KIND")

    def test_accidentally_attached_other_valid_claim(self):
        self.manifest["claims"][0]["ref"] = copy.deepcopy(self.manifest["claims"][1]["ref"])
        self.assertCode("CLAIM_REF")

    def test_claim_from_other_run(self):
        self.change_json("data/claims.json", "/420/run", "different-run")
        self.rehash()
        self.assertCode("CLAIM_RUN")

    def test_inactive_claim(self):
        self.change_json("data/claims.json", "/420/status", "superseded")
        self.rehash()
        self.assertCode("CLAIM_STATUS")

    def test_broken_hypothesis_ref(self):
        self.manifest["hypotheses"][0]["closing_ref"] = copy.deepcopy(self.manifest["hypotheses"][1]["closing_ref"])
        self.assertCode("HYPOTHESIS_REF")

    def test_hypothesis_edge_sources_must_match_claim(self):
        self.manifest["hypotheses"][0]["claim_links"][0]["source_ids"] = ["FIN-003"]
        self.assertCode("SOURCE_MISMATCH")

    def test_shared_citations_are_checked_against_original_closing(self):
        self.manifest["hypotheses"][0]["claim_links"][1]["shared_closing_source_ids"].append("NOV-M07")
        self.assertCode("SOURCE_MISMATCH")

    def test_broken_action_hypothesis(self):
        self.manifest["actions"][0]["hypothesis_ids"].append("OPEN-MISSING")
        self.assertCode("UNKNOWN_HYPOTHESIS")

    def test_action_with_unrelated_valid_claim(self):
        self.manifest["actions"][0]["claim_ids"].append("C-432")
        self.assertCode("ACTION_CLAIM")

    def test_action_cannot_name_hypothesis_without_connected_claim(self):
        self.manifest["actions"][0]["hypothesis_ids"].append("OPEN-HAN-01")
        self.assertCode("ACTION_HYPOTHESIS")

    def test_action_cannot_use_another_groups_original(self):
        self.manifest["actions"][0]["ref"] = copy.deepcopy(self.manifest["actions"][6]["ref"])
        self.assertCode("ACTION_GROUP")

    def test_action_missing_from_scope(self):
        self.manifest["actions"].pop()
        self.assertCode("SCOPE")

    def test_scope_cannot_silently_omit_a_current_run_claim(self):
        self.manifest["scope"]["claims"].remove("C-421")
        self.manifest["claims"] = [x for x in self.manifest["claims"] if x["id"] != "C-421"]
        self.assertCode("RUN_CLAIM_SCOPE")

    def test_duplicate_claim(self):
        self.manifest["claims"].append(copy.deepcopy(self.manifest["claims"][0]))
        self.assertCode("DUPLICATE")

    def test_duplicate_action_reference(self):
        self.manifest["actions"][1]["ref"] = copy.deepcopy(self.manifest["actions"][0]["ref"])
        self.assertCode("DUPLICATE")

    def test_orphan_claim(self):
        for hyp in self.manifest["hypotheses"]:
            hyp["claim_links"] = [x for x in hyp["claim_links"] if x["claim_id"] != "C-421"]
        self.assertCode("ORPHAN_CLAIM")

    def test_orphan_hypothesis(self):
        for action in self.manifest["actions"]:
            action["hypothesis_ids"] = [x for x in action["hypothesis_ids"] if x != "OPEN-ENV-01"]
        self.assertCode("ORPHAN_HYPOTHESIS")

    def test_missing_next_observation_even_after_rehash(self):
        self.change_json("data/outlook_2027_reassessment.json", "/closing/judgments/0/next_observations", [])
        self.rehash()
        self.assertCode("NEXT_OBSERVATION")

    def test_next_observation_cannot_point_to_unrelated_nonempty_text_list(self):
        hyp = self.manifest["hypotheses"][0]
        hyp["next_observations_ref"] = copy.deepcopy(hyp["closing_sources_ref"])
        self.assertCode("HYPOTHESIS_FIELD")

    def test_missing_alternative_even_after_rehash(self):
        self.change_json("data/outlook_2027_reassessment.json", "/closing/judgments/0/strongest_alternative", "")
        self.rehash()
        self.assertCode("ALTERNATIVE")

    def test_claim_hypothesis_needs_next_observation(self):
        self.change_json("data/claims.json", "/421/next_observation", "")
        self.rehash()
        self.assertCode("HYPOTHESIS_FIELD")

    def test_unread_source_cannot_back_a_fact(self):
        source = self.manifest["claims"][0]["source_ids"][0]
        sources = json.loads((self.root / "data/sources.json").read_text(encoding="utf-8"))
        idx = next(i for i, row in enumerate(sources) if row["id"] == source)
        self.change_json("data/sources.json", f"/{idx}/read_status", "unread")
        self.change_json("data/claims.json", "/420/kind", "fact")
        self.manifest["claims"][0]["kind"] = "fact"
        self.rehash()
        self.assertCode("UNREAD_FACT")

    def test_bad_type_fails_as_validation_error(self):
        self.manifest["hypotheses"][0]["claim_links"] = "C-421"
        self.assertCode("TYPE")
        with self.assertRaises(ValueError):
            lineage.validate(self.root, self.manifest)

    def test_correction_must_match_same_original_event_and_source_scope(self):
        self.manifest["read_status_corrections"][0]["source_scope_ref"] = copy.deepcopy(
            self.manifest["read_status_corrections"][1]["source_scope_ref"])
        self.assertCode("CORRECTION_BASIS")

    def test_correction_cannot_claim_new_read_or_full_text(self):
        fix = self.manifest["read_status_corrections"][0]
        fix["new_read_performed"] = True
        fix["corrected_read_status"] = "full_text"
        self.assertCode("CORRECTION_REASON")
        self.assertCode("CORRECTION_PRECONDITION")

    def test_original_event_change_detected(self):
        self.change_json(self.manifest["read_events"]["path"], "/read_events/0/summary", "Changed original")
        self.assertCode("REF_HASH")

    def test_original_action_section_change_detected(self):
        path = self.root / self.manifest["actions"][3]["ref"]["path"]
        text = path.read_text(encoding="utf-8")
        heading = self.manifest["actions"][3]["ref"]["heading"]
        path.write_text(text.replace(heading, heading + "\nChanged original action", 1), encoding="utf-8")
        self.assertCode("REF_HASH")

    def test_context_only_sources_must_be_accounted_for(self):
        self.manifest["context_only_read_source_ids"] = []
        self.assertCode("CONTEXT_SOURCE")

    def test_data_override_checks_proposed_registry_without_writing(self):
        claims_path = self.root / "data/claims.json"
        before = claims_path.read_bytes()
        claims = json.loads(before)
        self.assertTrue(lineage.validate(self.root, self.manifest, data_override={"claims": claims})["valid"])
        claims[420]["source_ids"] = ["SOURCE-MISSING"]
        with self.assertRaises(ValueError):
            lineage.validate(self.root, self.manifest, data_override={"claims": claims})
        self.assertEqual(claims_path.read_bytes(), before)

    def test_manifest_paths_cannot_escape_or_include_private_absolute_paths(self):
        self.manifest["claims"][0]["ref"]["path"] = "../outside.json"
        self.assertCode("MANIFEST")
        self.manifest["claims"][0]["ref"]["path"] = "C:/private/file.json"
        self.assertCode("MANIFEST")

    def test_invalid_json_pointer_index_is_rejected(self):
        self.manifest["claims"][0]["ref"]["pointer"] = "/-1"
        self.assertCode("REF")

    def test_cli_success_and_failure_exit_codes(self):
        base = [sys.executable, str(REPO / "scripts/lineage.py"), "--root", str(self.root), "--manifest", MANIFEST]
        good = subprocess.run(base, capture_output=True, encoding="utf-8")
        self.assertEqual(good.returncode, 0, good.stderr + good.stdout)
        self.assertTrue(json.loads(good.stdout)["valid"])
        self.manifest["read_status_corrections"] = []
        write_json(self.root / MANIFEST, self.manifest)
        bad = subprocess.run(base, capture_output=True, encoding="utf-8")
        self.assertEqual(bad.returncode, 1)
        self.assertFalse(json.loads(bad.stdout)["valid"])


if __name__ == "__main__":
    unittest.main()
