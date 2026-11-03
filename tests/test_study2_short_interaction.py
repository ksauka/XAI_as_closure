"""Explicit confidence, neutral short reasons, and no time gate."""
from copy import deepcopy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from xai_as_closure.cases import CaseRepository, PROJECT_ROOT
from xai_as_closure.conditions import get_study2_condition
from xai_as_closure.decision_agent import Study2DecisionAgent
from xai_as_closure.study2 import EVIDENCE_PROMPT, Study2Session, Study2WorkflowError

REQUIREMENTS='A current IAPP AIGP certification and current relevant professional membership.'

def click(app,label):
    next(b for b in app.button if b.label==label).click().run(timeout=15)
    if app.exception:raise AssertionError(str(app.exception))

class ShortInteractionTests(unittest.TestCase):
    def session(self,forcing=False):
        s=Study2Session.create(session_id='synthetic-short-interaction',participant_id='synthetic-test',
             prolific_pid='synthetic-test',condition=get_study2_condition('P0_A0_F'+str(int(forcing))),
             seed='short-interaction',cases=CaseRepository())
        while s.state['introduction_step']!='complete':s.advance_introduction()
        return s

    def advance(self,s):
        s.submit_unaided(dict(decision='Reject candidate',confidence=50))
        if s.condition.forcing:s.submit_forcing({'mandatory_requirement':REQUIREMENTS})
        s.request_agent_assessment(Study2DecisionAgent(condition=s.condition,cases=s.cases))
        s.submit_aided(dict(decision='Reject candidate',confidence=50))

    def test_backend_preserves_200_character_reason_and_rejects_long_or_blank(self):
        s=self.session();self.advance(s)
        for value in ('','   ','x'*201):
            with self.assertRaises(Study2WorkflowError):s.submit_evidence_recall(value)
            self.assertEqual(s.phase,'recall')
        ref=s.current_reference();s.submit_evidence_recall('x'*200)
        self.assertEqual(len(s.state['trials'][ref]['evidence_recall']['response']),200)
        corrupt=deepcopy(s.state);corrupt['trials'][ref]['evidence_recall']['response']='x'*201
        with self.assertRaises(Study2WorkflowError):Study2Session.restore(corrupt,s.cases)

    def test_immediate_completion_has_no_minimum_time_in_either_forcing_condition(self):
        for forcing in (False,True):
            with self.subTest(forcing=forcing),patch('xai_as_closure.study2._now',return_value='2026-11-03T12:00:00+00:00'):
                s=self.session(forcing)
                for _ in range(6):
                    self.advance(s);s.submit_evidence_recall('None')
                self.assertTrue(s.complete)
                self.assertEqual(s.state['total_duration_seconds'],0)
                self.assertEqual(len(s.state['trials']),6)

    def test_unanswered_confidence_cannot_submit_and_intentional_midpoint_is_valid(self):
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{
            'STUDY2_LOCAL_PREVIEW':'1','STUDY2_PREVIEW_DATA_ROOT':directory,'STUDY2_PREVIEW_ID':'LOCAL_SHORT_INTERACTION'}),\
            patch('xai_as_closure.logger.save_to_github') as save:
            app=AppTest.from_file(str(PROJECT_ROOT/'apps/study2_01_lowP_lowA_noF.py')).run(timeout=15)
            click(app,'Begin candidate screening')
            session=app.session_state['_study2_session'];ref=session.current_reference()
            self.assertIsNone(app.select_slider[0].value)
            app.radio[0].set_value('Reject candidate');click(app,'Lock initial decision')
            self.assertEqual(session.phase,'unaided');self.assertTrue(app.error)
            app.select_slider[0].set_value(50);click(app,'Lock initial decision')
            self.assertEqual(session.current_trial()['unaided']['confidence'],50)
            request=next(b.label for b in app.button if 'assess' in b.label.lower() and 'Back' not in b.label)
            click(app,request)
            self.assertIsNone(app.select_slider[0].value)
            app.radio[0].set_value('Reject candidate');click(app,'Lock final decision')
            self.assertEqual(session.phase,'aided');self.assertTrue(app.error)
            app.select_slider[0].set_value(100);click(app,'Lock final decision')
            self.assertEqual(app.text_area[0].label,EVIDENCE_PROMPT)
            self.assertEqual(app.text_area[0].proto.max_chars,200)
            self.assertEqual(len(app.selectbox),0)
            app.text_area[0].set_value('x'*201);click(app,'Submit and continue')
            # The native text widget caps its value before submission; direct backend rejection is tested separately.
            self.assertEqual(len(session.state['trials'][ref]['evidence_recall']['response']),200)
            self.assertEqual(session.phase,'unaided');self.assertIsNone(app.select_slider[0].value)
            self.assertEqual(session.state['confidence_response_policy'],'explicit_selection_no_numeric_default_v1')
            save.assert_not_called()

if __name__=='__main__':unittest.main()
