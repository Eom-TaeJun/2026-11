import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("research", Path(__file__).parents[1] / "scripts" / "research.py")
research = importlib.util.module_from_spec(spec)
spec.loader.exec_module(research)


def fixture():
    return {"sources": [{"id": "SRC-1", "title": "Redemption", "publisher": "Example", "url": "https://example.org/report", "visibility": "public", "checked_at": "2026-11-02", "published_at": None, "read_status": "selected_sections", "read_scope": "section 2", "summary": "redemption cash", "used_for": "liquidity question", "limitations": "no measured outcome", "topic_ids": ["T-CASH"]}], "claims": [{"id": "C-1", "kind": "hypothesis", "status": "active", "text": "Cash conditions matter", "source_ids": ["SRC-1"], "topic_ids": ["T-CASH"], "limitations": "conditional", "alternative": "existing rail", "next_observation": "bank receipt"}], "topics": [{"id": "T-CASH", "name": "Cash", "question": "When is cash available?"}]}


class IntegrityTests(unittest.TestCase):
    def test_topic_and_cross_category_id_validation(self):
        data = fixture()
        del data["topics"][0]["name"]
        self.assertTrue(any("topic name" in x for x in research.errors(data)))
        data = fixture()
        data["topics"][0]["id"] = "SRC-1"
        self.assertTrue(any("unique across" in x for x in research.errors(data)))

    def test_unchanged_batch_repairs_missing_generated_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = fixture()
            for k, v in data.items():
                research.write_json(root / "data" / f"{k}.json", v)
            batch = root / "batch.json"
            research.write_json(batch, {"change_reason": "retry after interruption"})
            self.assertEqual(research.ingest(root, batch)["status"], "unchanged")
            self.assertTrue((root / "sources" / "cards" / "SRC-1.md").exists())

    def test_encoded_links_and_repository_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            (root / "A B.md").write_text("ok")
            (root / "index.md").write_text("[good](A%20B.md)")
            self.assertEqual(research.check_links(root), [])
            (root.parent / "outside.txt").write_text("not a repository artifact")
            (root / "index.md").write_text("[bad](../outside.txt)")
            self.assertTrue(any("outside repository" in x for x in research.check_links(root)))

    def test_unread_source_cannot_support_fact(self):
        data = fixture()
        data["sources"][0]["read_status"] = "unread"
        data["claims"][0]["kind"] = "fact"
        self.assertTrue(any("unread source" in x for x in research.errors(data)))

    def test_private_evidence_rejected(self):
        data = fixture()
        data["sources"][0]["visibility"] = "private"
        self.assertTrue(any("public evidence" in x for x in research.errors(data)))

    def test_missing_provenance_and_unknown_reference(self):
        data = fixture()
        data["claims"][0]["source_ids"] = ["MISSING"]
        self.assertTrue(any("unknown source" in x for x in research.errors(data)))

    def test_hypothesis_requires_discriminating_observation(self):
        data = fixture()
        del data["claims"][0]["next_observation"]
        self.assertTrue(any("next observation" in x for x in research.errors(data)))

    def test_correction_preserves_prior_and_rejects_bad_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = fixture()
            for k, v in data.items():
                research.write_json(root / "data" / f"{k}.json", v)
            claim = copy.deepcopy(data["claims"][0])
            claim["text"] = "Corrected interpretation"
            batch = root / "batch.json"
            research.write_json(batch, {"change_reason": "New section read", "claims": [claim]})
            result = research.ingest(root, batch)
            self.assertEqual(result["status"], "updated")
            log = research.read_json(next((root / "history").glob("*.json")))
            self.assertEqual(log["before"]["claims"][0]["text"], "Cash conditions matter")
            self.assertEqual(research.ingest(root, batch)["status"], "unchanged")
            state = (root / "data" / "claims.json").read_bytes()
            claim["source_ids"] = ["MISSING"]
            research.write_json(batch, {"change_reason": "bad", "claims": [claim]})
            with self.assertRaises(ValueError):
                research.ingest(root, batch)
            self.assertEqual(state, (root / "data" / "claims.json").read_bytes())

    def test_graph_expansion_returns_traceable_neighbors(self):
        data = fixture()
        other = dict(data["sources"][0], id="SRC-2", title="Regulation", url="https://example.org/other", summary="law", used_for="capital")
        data["sources"].append(other)
        data["claims"][0]["source_ids"].append("SRC-2")
        result = research.search(data, "redemption", mode="graph", limit=5)
        self.assertEqual([x["id"] for x in result], ["SRC-1", "SRC-2"])
        self.assertEqual(result[1]["via"], "shared_claim")


if __name__ == "__main__":
    unittest.main()
