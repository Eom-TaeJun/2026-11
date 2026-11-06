"""Failure injection only in temporary checkouts; no live research ledgers."""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).parents[1] / "scripts" / "research.py"
spec = importlib.util.spec_from_file_location("recovery_research", SCRIPT)
research = importlib.util.module_from_spec(spec)
spec.loader.exec_module(research)
fixture_spec = importlib.util.spec_from_file_location("existing_research_tests", Path(__file__).with_name("test_research.py"))
fixtures = importlib.util.module_from_spec(fixture_spec)
fixture_spec.loader.exec_module(fixtures)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.before = fixtures.fixture()
        for key, value in self.before.items():
            research.write_json(self.root / "data" / f"{key}.json", value)
        research.build(self.root)
        self.after = copy.deepcopy(self.before)
        self.after["sources"][0]["summary"] = "Corrected evidence"
        self.after["claims"][0]["text"] = "Corrected interpretation"
        self.after["topics"][0]["question"] = "When does corrected cash arrive?"
        self.batch = self.root / "batch.json"
        research.write_json(self.batch, {"change_reason": "correction", **self.after})

    def history(self):
        return list((self.root / "history").glob("*.json"))

    def journal(self):
        return list((self.root / "history" / "transactions").glob("*.json"))

    def files(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}

    def interrupt_after(self, relative):
        real_write = research._atomic_write

        def interrupted(path, raw):
            real_write(path, raw)
            if Path(path) == self.root / relative:
                raise OSError("simulated process interruption")

        with patch.object(research, "_atomic_write", side_effect=interrupted):
            with self.assertRaisesRegex(OSError, "simulated"):
                research.ingest(self.root, self.batch)

    def finish_and_assert(self):
        frozen_journal = self.journal()[0].read_bytes()
        frozen_history = self.history()[0].read_bytes()
        self.assertEqual(research.ingest(self.root, self.batch)["status"], "updated")
        self.assertEqual(research.load(self.root), self.after)
        self.assertFalse(research.has_pending(self.root))
        self.assertEqual(self.journal()[0].read_bytes(), frozen_journal)
        self.assertEqual(self.history()[0].read_bytes(), frozen_history)
        self.assertEqual(research.read_json(self.history()[0])["before"], self.before)
        self.assertEqual(research.ingest(self.root, self.batch)["status"], "unchanged")
        self.assertEqual(len(self.history()), 1)
        self.assertEqual(len(self.journal()), 1)
        for relative, expected in research._render(self.after).items():
            self.assertEqual((self.root / relative).read_bytes(), expected)

    def test_resume_after_first_core_write_and_readers_refuse_mixed_state(self):
        self.interrupt_after("data/sources.json")
        self.assertEqual(research.read_json(self.root / "data/sources.json"), self.after["sources"])
        self.assertEqual(research.read_json(self.root / "data/claims.json"), self.before["claims"])
        self.assertTrue(research.has_pending(self.root))
        for operation in (research.load, research.build):
            with self.assertRaisesRegex(ValueError, "Incomplete research transaction"):
                operation(self.root)
        for args in (["validate"], ["search", "cash"], ["build"]):
            result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root), *args], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Incomplete research transaction", result.stderr)
        self.finish_and_assert()

    def test_resume_after_second_core_write(self):
        self.interrupt_after("data/claims.json")
        self.assertEqual(research.read_json(self.root / "data/topics.json"), self.before["topics"])
        self.finish_and_assert()

    def test_resume_after_generated_write(self):
        self.interrupt_after("sources/cards/SRC-1.md")
        self.assertEqual(research._load_unlocked(self.root), self.after)
        self.finish_and_assert()

    def test_resume_after_history_write(self):
        real_write = research._atomic_write

        def fail_history(path, raw):
            real_write(path, raw)
            if Path(path).parent == self.root / "history" and Path(path).suffix == ".json":
                raise OSError("history interruption")

        with patch.object(research, "_atomic_write", side_effect=fail_history):
            with self.assertRaises(OSError):
                research.ingest(self.root, self.batch)
        self.assertEqual(research._load_unlocked(self.root), self.before)
        self.finish_and_assert()

    def test_completion_marker_failure_resumes_without_second_history(self):
        real_write = research._atomic_write

        def fail_marker(path, raw):
            if Path(path).suffix == ".done":
                raise OSError("completion interruption")
            real_write(path, raw)

        with patch.object(research, "_atomic_write", side_effect=fail_marker):
            with self.assertRaises(OSError):
                research.ingest(self.root, self.batch)
        self.assertTrue(research.has_pending(self.root))
        self.finish_and_assert()

    def test_interruption_after_journal_creation_resumes_original_before(self):
        real_write = research._atomic_write

        def fail_prepared(path, raw):
            real_write(path, raw)
            if Path(path).parent.name == "transactions" and Path(path).suffix == ".json":
                raise OSError("prepared interruption")

        with patch.object(research, "_atomic_write", side_effect=fail_prepared):
            with self.assertRaises(OSError):
                research.ingest(self.root, self.batch)
        self.assertTrue(research.has_pending(self.root))
        self.assertEqual(self.history(), [])
        self.assertEqual(research._load_unlocked(self.root), self.before)
        self.assertEqual(research.ingest(self.root, self.batch)["status"], "updated")
        self.assertEqual(research.read_json(self.history()[0])["before"], self.before)
        self.assertEqual(len(self.history()), 1)

    def test_other_batch_or_changed_frozen_bytes_are_rejected_without_writes(self):
        self.interrupt_after("data/sources.json")
        other = self.root / "other.json"
        other.write_bytes(self.batch.read_bytes() + b" ")  # Same JSON, different frozen bytes.
        before = self.files()
        with self.assertRaisesRegex(ValueError, "Another batch"):
            research.ingest(self.root, other)
        self.assertEqual(self.files(), before)
        self.finish_and_assert()

    def test_external_core_edit_is_not_overwritten_and_no_recovery_targets_advance(self):
        self.interrupt_after("data/sources.json")
        changed = copy.deepcopy(self.before["claims"])
        changed[0]["text"] = "Independent user edit"
        research.write_json(self.root / "data/claims.json", changed)
        before = self.files()
        with self.assertRaisesRegex(ValueError, "Recovery conflict: data/claims.json"):
            research.ingest(self.root, self.batch)
        self.assertEqual(self.files(), before)

    def test_external_generated_edit_is_not_overwritten(self):
        self.interrupt_after("data/claims.json")
        (self.root / "sources/cards/SRC-1.md").write_text("manual card correction", encoding="utf-8")
        before = self.files()
        with self.assertRaisesRegex(ValueError, "Recovery conflict: sources/cards"):
            research.ingest(self.root, self.batch)
        self.assertEqual(self.files(), before)

    def test_completed_old_batch_cannot_roll_back_later_research(self):
        research.ingest(self.root, self.batch)
        later = copy.deepcopy(self.after["claims"][0])
        later["text"] = "Newer research"
        other = self.root / "newer.json"
        research.write_json(other, {"change_reason": "newer evidence", "claims": [later]})
        research.ingest(self.root, other)
        before = self.files()
        with self.assertRaisesRegex(ValueError, "Completed batch is stale"):
            research.ingest(self.root, self.batch)
        self.assertEqual(self.files(), before)

    def test_record_bearing_noop_gets_replay_protection_but_empty_noop_does_not(self):
        noop = self.root / "noop.json"
        research.write_json(noop, {"change_reason": "no content change"})
        self.assertEqual(research.ingest(self.root, noop)["status"], "unchanged")
        self.assertEqual(self.journal(), [])
        research.write_json(noop, {"change_reason": "existing version", **self.before})
        self.assertEqual(research.ingest(self.root, noop)["status"], "unchanged")
        self.assertEqual(len(self.journal()), 1)
        self.assertEqual(self.history(), [])
        research.ingest(self.root, self.batch)
        with self.assertRaisesRegex(ValueError, "Completed batch is stale"):
            research.ingest(self.root, noop)

    def test_completed_batch_missing_generated_file_repair_is_resumable(self):
        research.ingest(self.root, self.batch)
        (self.root / "sources/cards/SRC-1.md").unlink()
        self.interrupt_after("sources/cards/SRC-1.md")
        self.assertTrue(research.has_pending(self.root))
        result = research.ingest(self.root, self.batch,
            expected_before_sha256=research._state_hash(self.before),
            expected_after_sha256=research._state_hash(self.after))
        self.assertEqual(result["status"], "unchanged")
        self.assertFalse(research.has_pending(self.root))
        self.assertEqual(len(self.history()), 1)

    def test_expected_hashes_reject_stale_plan_before_any_mutation(self):
        before = self.files()
        with self.assertRaisesRegex(ValueError, "Stale plan"):
            research.ingest(self.root, self.batch, expected_before_sha256="0" * 64,
                expected_after_sha256=research._state_hash(self.after))
        self.assertEqual(self.files(), before)
        with self.assertRaisesRegex(ValueError, "Stale plan"):
            research.ingest(self.root, self.batch, expected_before_sha256=research._state_hash(self.before),
                expected_after_sha256="0" * 64)
        self.assertEqual(self.files(), before)

    def test_expected_hashes_checked_against_pending_journal(self):
        self.interrupt_after("data/claims.json")
        before = self.files()
        with self.assertRaisesRegex(ValueError, "Stale plan"):
            research.ingest(self.root, self.batch, expected_before_sha256="0" * 64,
                expected_after_sha256=research._state_hash(self.after))
        self.assertEqual(self.files(), before)
        result = research.ingest(self.root, self.batch, expected_before_sha256=research._state_hash(self.before),
            expected_after_sha256=research._state_hash(self.after))
        self.assertEqual(result["status"], "updated")

    def test_corrupt_journal_is_not_treated_as_valid_or_overwritten(self):
        self.interrupt_after("data/sources.json")
        journal = self.journal()[0]
        envelope = research.read_json(journal)
        envelope["payload"]["after"]["claims"][0]["text"] = "tampered"
        research.write_json(journal, envelope)
        before = self.files()
        for operation in (research.load, research.build):
            with self.assertRaisesRegex(ValueError, "Invalid recovery journal"):
                operation(self.root)
        with self.assertRaisesRegex(ValueError, "Invalid recovery journal"):
            research.ingest(self.root, self.batch)
        self.assertEqual(self.files(), before)

    def test_invalid_batch_is_validated_before_journal_or_core_writes(self):
        batch = research.read_json(self.batch)
        batch["claims"][0]["source_ids"] = ["MISSING"]
        research.write_json(self.batch, batch)
        before = self.files()
        with self.assertRaisesRegex(ValueError, "unknown source"):
            research.ingest(self.root, self.batch)
        self.assertEqual(self.files(), before)

    def test_atomic_replace_failure_preserves_old_bytes(self):
        target = self.root / "data/claims.json"
        before = target.read_bytes()
        with patch.object(research.os, "replace", side_effect=OSError("replace interrupted")):
            with self.assertRaises(OSError):
                research.write_json(target, self.after["claims"])
        self.assertEqual(target.read_bytes(), before)
        self.assertFalse(list(target.parent.glob("*.tmp")))

    def test_os_lock_rejects_overlap_then_releases_without_deleting_file(self):
        lock = self.root / "history/.research.lock"
        with research.writer_lock(self.root):
            result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root), "validate"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("writer is busy", result.stderr)
        self.assertTrue(lock.exists())
        self.assertEqual(research.load(self.root), self.before)
        self.assertTrue(lock.exists())

    def test_os_lock_releases_on_abrupt_process_exit_without_stale_deletion(self):
        code = "\n".join([
            "import importlib.util, os, sys",
            "from pathlib import Path",
            "s=importlib.util.spec_from_file_location('research',sys.argv[1])",
            "r=importlib.util.module_from_spec(s); s.loader.exec_module(r)",
            "with r.writer_lock(Path(sys.argv[2])):",
            "    os._exit(0)",
        ])
        result = subprocess.run([sys.executable, "-c", code, str(SCRIPT), str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / "history/.research.lock").exists())
        self.assertEqual(research.load(self.root), self.before)


if __name__ == "__main__":
    unittest.main()
