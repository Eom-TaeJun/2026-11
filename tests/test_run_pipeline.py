"""Behavioral pipeline tests with real ingestion and lineage on temporary data."""
import copy
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import run_pipeline as pipeline
from legacy_run_guard import stop_archived_run

spec = importlib.util.spec_from_file_location("pipeline_fixtures", Path(__file__).with_name("test_lineage.py"))
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
research = pipeline.research


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.manifest = fixtures.make_fixture(self.root)
        research.build(self.root)
        self.batch = {"change_reason": "Test update"}
        self.plan = "runs/pipeline/test-run/plan.json"

    def save(self, path, value):
        pipeline._write(self.root / path, value)

    def changed_claim(self):
        claim = copy.deepcopy(research.load(self.root)["claims"][0])
        claim["text"] = "Revised conditional cash view"
        self.batch["claims"] = [claim]
        manifest = research.read_json(self.root / self.manifest)
        manifest["claims"][0]["ref"]["sha256"] = pipeline.lineage.digest(claim)
        self.save(self.manifest, manifest)

    def prepare(self):
        self.save("batch.json", self.batch)
        return pipeline.prepare(self.root, "test-run", "batch.json", self.manifest)

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*")
                if p.is_file() and p.suffix != ".lock"}

    def test_replay_preserves_claim_ids_history_and_complete_state(self):
        self.changed_claim()
        self.prepare()
        pipeline.apply(self.root, self.plan)
        before = self.snapshot()
        self.assertEqual(self.prepare()["status"], "already_prepared")
        self.assertEqual(pipeline.apply(self.root, self.plan)["status"], "complete")
        self.assertEqual(before, self.snapshot())
        self.assertEqual(len(list((self.root / "history").glob("*.json"))), 1)
        self.assertEqual([c["id"] for c in research.load(self.root)["claims"]], ["C-1"])

    def test_checkpoint_failure_after_ingest_resumes_without_new_history(self):
        self.changed_claim()
        self.prepare()
        original = pipeline._checkpoint
        def fail(path, envelope, phase):
            if phase == "ingested":
                raise OSError("Injected checkpoint interruption")
            return original(path, envelope, phase)
        with patch.object(pipeline, "_checkpoint", side_effect=fail):
            with self.assertRaisesRegex(OSError, "checkpoint"):
                pipeline.apply(self.root, self.plan)
        self.assertEqual(research.read_json(self.root / self.plan.replace("plan.json", "state.json"))["phase"], "prepared")
        pipeline.apply(self.root, self.plan)
        self.assertEqual(len(list((self.root / "history").glob("*.json"))), 1)

    def test_partial_core_write_is_resumed_from_frozen_batch(self):
        self.changed_claim()
        self.prepare()
        original = research._atomic_write
        def fail(path, raw):
            if Path(path) == self.root / "data/graph.json":
                raise OSError("Injected graph interruption")
            return original(path, raw)
        with patch.object(research, "_atomic_write", side_effect=fail):
            with self.assertRaisesRegex(OSError, "graph"):
                pipeline.apply(self.root, self.plan)
        self.assertTrue(research.has_pending(self.root))
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            research.load(self.root)
        pipeline.apply(self.root, self.plan)
        self.assertFalse(research.has_pending(self.root))
        self.assertEqual(len(list((self.root / "history").glob("*.json"))), 1)

    def test_build_failure_does_not_acknowledge_completion(self):
        self.prepare()
        with patch.object(research, "build", side_effect=OSError("Injected build failure")):
            with self.assertRaisesRegex(OSError, "build"):
                pipeline.apply(self.root, self.plan)
        state = research.read_json(self.root / self.plan.replace("plan.json", "state.json"))
        self.assertEqual(state["phase"], "lineage_validated")
        self.assertEqual(pipeline.apply(self.root, self.plan)["status"], "complete")

    def test_changed_frozen_input_is_rejected_even_after_completion(self):
        self.prepare()
        pipeline.apply(self.root, self.plan)
        self.save("runs/events.json", {"read_events": []})
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "Frozen lineage input changed"):
            pipeline.apply(self.root, self.plan)
        self.assertEqual(before, self.snapshot())

    def test_changed_batch_and_reused_id_rejected(self):
        self.prepare()
        self.batch["change_reason"] = "Different request"
        self.save("batch.json", self.batch)
        with self.assertRaisesRegex(ValueError, "different inputs"):
            pipeline.prepare(self.root, "test-run", "batch.json", self.manifest)
        self.save("runs/pipeline/test-run/batch.json", self.batch)
        with self.assertRaisesRegex(ValueError, "Frozen batch changed"):
            pipeline.apply(self.root, self.plan)

    def test_old_completed_plan_cannot_overwrite_later_research(self):
        self.changed_claim()
        self.prepare()
        pipeline.apply(self.root, self.plan)
        topics = research.load(self.root)["topics"]
        topics[0]["question"] = "A later investigation"
        self.save("data/topics.json", topics)
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "Stale plan"):
            pipeline.apply(self.root, self.plan)
        self.assertEqual(before, self.snapshot())

    def test_frozen_batch_line_ending_change_is_rejected_before_core_resume(self):
        self.changed_claim()
        self.prepare()
        original_write = research._atomic_write
        def fail(path, raw):
            if Path(path) == self.root / "data/graph.json":
                raise OSError("Injected interruption")
            return original_write(path, raw)
        with patch.object(research, "_atomic_write", side_effect=fail), self.assertRaises(OSError):
            pipeline.apply(self.root, self.plan)
        frozen = self.root / self.plan.replace("plan.json", "batch.json")
        original = frozen.read_bytes()
        frozen.write_bytes(original.replace(b"\n", b"\r\n"))
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "exact original LF bytes"):
            pipeline.apply(self.root, self.plan)
        self.assertEqual(before, self.snapshot())
        frozen.write_bytes(original)
        self.assertEqual(pipeline.apply(self.root, self.plan)["status"], "complete")

    def test_invalid_lineage_stops_before_prepare_mutations(self):
        manifest = research.read_json(self.root / self.manifest)
        manifest["actions"][0]["hypothesis_ids"] = ["MISSING"]
        self.save(self.manifest, manifest)
        self.save("batch.json", self.batch)
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "UNKNOWN_HYPOTHESIS"):
            pipeline.prepare(self.root, "test-run", "batch.json", self.manifest)
        self.assertEqual(before, self.snapshot())

    def test_batch_claim_cannot_bypass_lineage_scope(self):
        claim = copy.deepcopy(research.load(self.root)["claims"][0])
        claim.update(id="C-2", run="another-run")
        self.batch["claims"] = [claim]
        with self.assertRaisesRegex(ValueError, "missing from lineage scope"):
            self.prepare()
        self.assertEqual(len(research.load(self.root)["claims"]), 1)

    def test_invalid_checkpoint_stops_before_ingestion(self):
        self.changed_claim()
        self.prepare()
        self.save(self.plan.replace("plan.json", "state.json"), {"phase": "complete", "plan_sha256": "wrong"})
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "Checkpoint"):
            pipeline.apply(self.root, self.plan)
        self.assertEqual(before, self.snapshot())

    def test_alternate_registry_cannot_pass_preflight_then_fail_after_write(self):
        self.changed_claim()
        manifest = research.read_json(self.root / self.manifest)
        manifest["registries"]["claims"]["path"] = "archive/claims.json"
        manifest["claims"][0]["ref"]["path"] = "archive/claims.json"
        self.save("archive/claims.json", research.load(self.root)["claims"])
        self.save(self.manifest, manifest)
        self.save("batch.json", self.batch)
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "must match ingestion"):
            pipeline.prepare(self.root, "test-run", "batch.json", self.manifest)
        self.assertEqual(before, self.snapshot())

    def test_lock_and_repository_boundary(self):
        self.prepare()
        with research.writer_lock(self.root / ".pipeline"):
            with self.assertRaisesRegex(ValueError, "busy"):
                pipeline.apply(self.root, self.plan)
        with self.assertRaisesRegex(ValueError, "escapes"):
            pipeline.apply(self.root, "../plan.json")

    def test_noop_creates_no_financial_history_or_journal(self):
        self.prepare()
        pipeline.apply(self.root, self.plan)
        self.assertEqual(list((self.root / "history").glob("*.json")), [])
        self.assertEqual(list((self.root / "history/transactions").glob("*.json")), [])


class ArchivedGuardTests(unittest.TestCase):
    def test_verified_archive_stops_before_old_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pipeline._write(root / "runs/old.json", {"run_id": "old", "status": "published_content_verified"})
            with redirect_stdout(io.StringIO()) as output, self.assertRaises(SystemExit) as exc:
                stop_archived_run(root, "old")
            self.assertEqual(exc.exception.code, 0)
            self.assertEqual(json.loads(output.getvalue())["status"], "archived_noop")

    def test_missing_or_unverified_archive_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for record in (None, {"run_id": "old", "status": "pending"}):
                if record:
                    pipeline._write(root / "runs/old.json", record)
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
                    stop_archived_run(root, "old")
                self.assertEqual(exc.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
