"""Tests for the active CHI 2027 Study 2 bounded agent and workflow."""

from __future__ import annotations

import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from xai_as_closure.cases import CaseRepository
from xai_as_closure.conditions import CONDITIONS, get_study2_condition
from xai_as_closure.decision_agent import Study2DecisionAgent
from xai_as_closure.logger import EventLogger, load_state
from xai_as_closure.study2 import Study2Session, Study2WorkflowError
from xai_as_closure.study2_app import _build_final_return
from xai_as_closure.study2_delivery import DELIVERY_SPEC_VERSION


class Study2AgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = CaseRepository()

    def test_all_eight_conditions_are_available(self) -> None:
        self.assertEqual(len(CONDITIONS), 8)
        self.assertEqual(
            {
                (
                    condition.provenance,
                    condition.anthropomorphic,
                    condition.forcing,
                )
                for condition in CONDITIONS.values()
            },
            {
                (provenance, anthropomorphic, forcing)
                for provenance in (False, True)
                for anthropomorphic in (False, True)
                for forcing in (False, True)
            },
        )

    def test_eight_condition_locked_entry_points_cover_the_matrix(self) -> None:
        app_root = Path(__file__).resolve().parents[1] / "apps"
        expected = {
            "study2_01_lowP_lowA_noF.py": "P0_A0_F0",
            "study2_02_lowP_lowA_F.py": "P0_A0_F1",
            "study2_03_lowP_highA_noF.py": "P0_A1_F0",
            "study2_04_lowP_highA_F.py": "P0_A1_F1",
            "study2_05_highP_lowA_noF.py": "P1_A0_F0",
            "study2_06_highP_lowA_F.py": "P1_A0_F1",
            "study2_07_highP_highA_noF.py": "P1_A1_F0",
            "study2_08_highP_highA_F.py": "P1_A1_F1",
        }
        observed = {path.name for path in app_root.glob("study2_*.py")}
        self.assertEqual(observed, set(expected))
        for filename, condition_id in expected.items():
            source = (app_root / filename).read_text(encoding="utf-8")
            self.assertIn(f'run("{condition_id}")', source)

    def test_agent_assesses_every_current_chi_profile(self) -> None:
        agent = Study2DecisionAgent(
            condition=get_study2_condition("P1_A1_F1"), cases=self.cases
        )
        for reference in self.cases.references:
            output = agent.assess(reference)
            self.assertEqual(output.reference, reference)
            self.assertTrue(output.recommendation)
            self.assertTrue(output.rationale)
            self.assertGreater(len(output.evaluation.retrieved_evidence), 0)
            self.assertGreater(len(output.visible_sources), 0)
        self.assertEqual(len(agent.assessment_history), 6)

    def test_conditions_change_rendering_only(self) -> None:
        for reference in self.cases.references:
            outputs = {
                condition_id: Study2DecisionAgent(
                    condition=condition, cases=self.cases
                ).assess(reference)
                for condition_id, condition in CONDITIONS.items()
            }
            self.assertEqual(
                len({output.recommendation for output in outputs.values()}), 1
            )
            self.assertEqual(len({output.rationale for output in outputs.values()}), 1)
            for condition_id, output in outputs.items():
                condition = CONDITIONS[condition_id]
                self.assertEqual(bool(output.visible_sources), condition.provenance)
                self.assertEqual(
                    output.delivery_preset.preset_id,
                    "HighA" if condition.anthropomorphic else "LowA",
                )
                self.assertEqual(
                    output.speaker_label,
                    "AI screening assistant"
                    if condition.anthropomorphic
                    else "AI screening system",
                )

    def test_agent_uses_only_current_chi_materials(self) -> None:
        output = Study2DecisionAgent(
            condition=get_study2_condition("P1_A0_F0"), cases=self.cases
        ).assess("C-01")
        serialized = str(output.audit_payload())
        self.assertIn("AI Governance Lead", serialized)


class Study2WorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = CaseRepository()

    @staticmethod
    def decision() -> dict:
        return {
            "decision": "Advance candidate to human interview",
            "confidence": 75,
        }

    def session(self, condition_id: str) -> Study2Session:
        session = Study2Session.create(
            session_id="s2_test",
            participant_id="participant-test",
            prolific_pid="participant-test",
            condition=get_study2_condition(condition_id),
            seed="participant-seed",
            cases=self.cases,
        )
        for _ in range(3):
            session.advance_introduction()
        return session

    def test_candidate_screening_is_gated_by_the_full_introduction(self) -> None:
        session = Study2Session.create(
            session_id="s2_intro",
            participant_id="participant-intro",
            prolific_pid="participant-intro",
            condition=get_study2_condition("P0_A0_F0"),
            seed="intro-test",
            cases=self.cases,
        )
        with self.assertRaisesRegex(Study2WorkflowError, "instructions"):
            session.submit_unaided(self.decision())
        self.assertEqual(session.advance_introduction(), "role")
        self.assertEqual(session.advance_introduction(), "policy")
        self.assertEqual(session.advance_introduction(), "complete")
        session.submit_unaided(self.decision())
        self.assertEqual(session.phase, "agent")

    def test_forcing_present_trial_sequence(self) -> None:
        session = self.session("P1_A1_F1")
        reference = session.current_reference()
        session.submit_unaided(self.decision())
        self.assertEqual(session.phase, "forcing")
        self.assertNotIn("agent_output", session.current_trial())
        with self.assertRaises(Study2WorkflowError):
            session.request_agent_assessment(
                Study2DecisionAgent(condition=session.condition, cases=self.cases)
            )
        session.submit_forcing(
            {
                "mandatory_requirement": (
                    "The candidate must hold AIGP or ISO/IEC 42001 Lead Implementer certification."
                )
            }
        )
        self.assertEqual(session.phase, "agent")
        output = session.request_agent_assessment(
            Study2DecisionAgent(condition=session.condition, cases=self.cases)
        )
        self.assertEqual(output.reference, reference)
        self.assertEqual(session.phase, "aided")
        session.submit_aided(self.decision())
        self.assertEqual(session.phase, "recall")
        session.submit_evidence_recall("The certification was decisive.")
        self.assertEqual(session.phase, "unaided")
        self.assertEqual(session.state["trial_index"], 1)

    def test_forcing_absent_skips_forcing_phase(self) -> None:
        session = self.session("P0_A0_F0")
        session.submit_unaided(self.decision())
        session.request_agent_assessment(
            Study2DecisionAgent(condition=session.condition, cases=self.cases)
        )
        self.assertEqual(session.phase, "aided")
        with self.assertRaises(Study2WorkflowError):
            session.submit_forcing({"mandatory_requirement": "AIGP"})

    def test_aided_response_records_recommendation_dwell(self) -> None:
        session = self.session("P0_A0_F0")
        session.submit_unaided(self.decision())
        session.request_agent_assessment(
            Study2DecisionAgent(condition=session.condition, cases=self.cases)
        )
        session.submit_aided(self.decision())
        self.assertGreaterEqual(
            session.current_trial()["aided"]["recommendation_dwell_seconds"], 0
        )

    def test_forcing_requires_a_substantive_typed_requirement(self) -> None:
        session = self.session("P0_A0_F1")
        session.submit_unaided(self.decision())
        with self.assertRaisesRegex(Study2WorkflowError, "Recheck"):
            session.submit_forcing({"mandatory_requirement": "AIGP"})
        self.assertEqual(session.phase, "forcing")
        self.assertNotIn("agent_output", session.current_trial())

    def test_all_six_trials_complete(self) -> None:
        session = self.session("P0_A0_F0")
        agent = Study2DecisionAgent(condition=session.condition, cases=self.cases)
        observed = []
        for _ in range(6):
            observed.append(session.current_reference())
            session.submit_unaided(self.decision())
            session.request_agent_assessment(agent)
            session.submit_aided(self.decision())
            session.submit_evidence_recall("The candidate evidence was decisive.")
        self.assertTrue(session.complete)
        self.assertEqual(set(observed), set(self.cases.references))
        self.assertEqual(len(session.state["trials"]), 6)
        self.assertIsNotNone(session.state["completed_at_utc"])

    def test_all_six_forcing_trials_complete_before_each_recommendation(self) -> None:
        session = self.session("P1_A1_F1")
        agent = Study2DecisionAgent(condition=session.condition, cases=self.cases)
        for _ in range(6):
            session.submit_unaided(self.decision())
            self.assertEqual(session.phase, "forcing")
            self.assertNotIn("agent_output", session.current_trial())
            session.submit_forcing(
                {
                    "mandatory_requirement": (
                        "The candidate must hold either AIGP or ISO/IEC 42001 "
                        "Lead Implementer certification."
                    )
                }
            )
            session.request_agent_assessment(agent)
            session.submit_aided(self.decision())
            session.submit_evidence_recall("The certification was decisive.")
        self.assertTrue(session.complete)
        restored = Study2Session.restore(deepcopy(session.state), self.cases)
        self.assertTrue(restored.complete)

    def test_restore_preserves_condition_and_order(self) -> None:
        session = self.session("P1_A0_F1")
        restored = Study2Session.restore(dict(session.state), self.cases)
        self.assertEqual(restored.condition.condition_id, "P1_A0_F1")
        self.assertEqual(restored.state["delivery_spec_version"], DELIVERY_SPEC_VERSION)
        self.assertEqual(
            restored.state["profile_order"], session.state["profile_order"]
        )

    def test_restore_rejects_pre_frozen_delivery_sessions(self) -> None:
        session = self.session("P1_A0_F1")
        session.state["schema_version"] = "study2-state-v2"
        session.state.pop("delivery_spec_version")
        with self.assertRaisesRegex(Study2WorkflowError, "unsupported Study 2 schema"):
            Study2Session.restore(deepcopy(session.state), self.cases)

    def test_restore_rejects_a_forcing_trial_that_skips_reencoding(self) -> None:
        session = self.session("P1_A0_F1")
        session.submit_unaided(self.decision())
        session.state["phase"] = "agent"
        with self.assertRaisesRegex(Study2WorkflowError, "requirement-reencoding"):
            Study2Session.restore(deepcopy(session.state), self.cases)


class Study2InfrastructureTests(unittest.TestCase):
    def test_study2_uses_the_hai_qualtrics_return_fields(self) -> None:
        return_url = _build_final_return(
            "https://example.qualtrics.com/jfe/form/SV_test",
            "prolific-test",
            "sessiontest",
            "P1_A0_F1",
        )
        self.assertIsNotNone(return_url)
        self.assertIn("PROLIFIC_PID=prolific-test", return_url or "")
        self.assertIn("session_id=sessiontest", return_url or "")
        self.assertIn("cond=P1_A0_F1", return_url or "")
        self.assertIn("done=1", return_url or "")
        self.assertIsNone(
            _build_final_return(
                "https://qualtrics.com.evil.test/form",
                "pid",
                "session",
                "P0_A0_F0",
            )
        )

    def test_hai_event_logger_writes_local_jsonl(self) -> None:
        condition = get_study2_condition("P1_A0_F1")
        with tempfile.TemporaryDirectory() as directory:
            logger = EventLogger(
                condition,
                "prolific-test",
                session_id="sessiontest",
                log_dir=Path(directory),
            )
            event = logger.log(
                "session_created",
                component="launch",
                payload={"condition_id": condition.condition_id},
            )
            self.assertEqual(event["schema_version"], "study2-event-v7")
            self.assertEqual(event["application_version"], "study2-app-v7")
            self.assertEqual(event["condition_id"], condition.condition_id)
            self.assertEqual(event["participant_id"], "prolific-test")
            self.assertEqual(logger.read_events(), [event])
            self.assertEqual(
                Path(directory).stat().st_mode & 0o777,
                0o700,
            )
            self.assertEqual(
                (Path(directory) / "sessiontest.jsonl").stat().st_mode & 0o777,
                0o600,
            )

    def test_interrupted_session_state_can_be_saved_and_reloaded(self) -> None:
        condition = get_study2_condition("P1_A0_F1")
        with tempfile.TemporaryDirectory() as directory:
            logger = EventLogger(
                condition,
                "prolific-test",
                session_id="sessiontest",
                log_dir=Path(directory),
            )
            self.assertIsNone(load_state("sessiontest", log_dir=Path(directory)))
            state = {"session_id": "sessiontest", "phase": "aided", "trial_index": 2}
            logger.save_state(state)
            reloaded = load_state("sessiontest", log_dir=Path(directory))
            self.assertEqual(reloaded, state)
            self.assertIsNone(load_state("no-such-session", log_dir=Path(directory)))

    def test_hai_logger_builds_and_pushes_private_github_payload(self) -> None:
        condition = get_study2_condition("P0_A0_F0")
        with tempfile.TemporaryDirectory() as directory:
            logger = EventLogger(
                condition,
                "prolific-test",
                session_id="sessiontest",
                log_dir=Path(directory),
            )
            logger.log("session_created")
            logger.session_meta = {"phase": "complete", "trials": {}}
            with patch(
                "xai_as_closure.logger.save_to_github",
                return_value=(True, None),
            ) as save:
                success = logger.push_to_github(
                    repo="owner/private-data",
                    github_token="secret-token",
                )
            self.assertTrue(success)
            self.assertIn("sessions/xai_as_closure/study2/", save.call_args.args[1])
            payload = logger.github_payload()
            self.assertEqual(payload["participant_id"], "prolific-test")
            self.assertEqual(payload["phase"], "complete")
            self.assertEqual(len(payload["events"]), 1)


if __name__ == "__main__":
    unittest.main()
