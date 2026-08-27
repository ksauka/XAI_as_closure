"""Regression coverage for participant-facing study documents."""

from __future__ import annotations

import unittest

from xai_as_closure.cases import ROLE_PATH, CaseRepository, CvSection, ParticipantCase
from xai_as_closure.document_renderer import (
    cv_document_html,
    reference_document_html,
    render_cv_document,
)


class _MarkdownRecorder:
    def __init__(self) -> None:
        self.values: list[tuple[str, bool]] = []

    def markdown(self, value: str, *, unsafe_allow_html: bool = False) -> None:
        self.values.append((value, unsafe_allow_html))


class DocumentRendererTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = CaseRepository()

    def test_cv_uses_the_locked_document_hierarchy_and_typography(self) -> None:
        case = self.cases.participant_case("C-01")
        recorder = _MarkdownRecorder()

        render_cv_document(
            recorder,
            case,
            role=self.cases.role,
            company=self.cases.company,
            timeline=self.cases.timeline,
        )

        self.assertEqual(len(recorder.values), 2)
        styles, document = (value for value, _unsafe in recorder.values)
        self.assertTrue(all(unsafe for _value, unsafe in recorder.values))
        self.assertIn('font-family: "Times New Roman", Times, serif', styles)
        self.assertIn("font-size: 16px !important", styles)
        self.assertIn("font-size: 14px !important", styles)
        self.assertIn("font-weight: 700 !important", styles)
        self.assertLess(
            document.index("Candidate details"),
            document.index('<article class="research-document'),
        )
        self.assertIn("Candidate reference", document)
        self.assertIn("C-01", document)
        self.assertIn("AI Governance Lead", document)
        self.assertIn("Suvh Trust Bank", document)
        self.assertIn("27–30 August 2026", document)
        self.assertIn("<h1>Education</h1>", document)
        self.assertIn("<h1>Experience</h1>", document)
        self.assertIn("<h2>Zenith Technical University</h2>", document)
        self.assertIn(
            "<h2>AI Governance Specialist, Halden Data Services (2021–present)</h2>",
            document,
        )
        self.assertIn("<em>Degree</em>:", document)
        self.assertIn("<em>Core Competencies</em>:", document)
        self.assertIn("<ul><li>Google Data Analytics", document)
        self.assertNotIn("cv_education", document)
        self.assertNotIn("CV(2)", document)

    def test_cv_focus_highlights_a_passage_without_changing_its_heading(self) -> None:
        document = cv_document_html(
            self.cases.participant_case("C-01"),
            role=self.cases.role,
            company=self.cases.company,
            timeline=self.cases.timeline,
            focus="3.1",
        )

        self.assertIn("research-document__focus", document)
        self.assertIn("Cited passage", document)
        self.assertIn(
            "<h2>AI Governance Specialist, Halden Data Services (2021–present)</h2>",
            document,
        )

    def test_reference_document_uses_the_same_paper_structure(self) -> None:
        document = reference_document_html(
            ROLE_PATH.read_text(encoding="utf-8"),
            document_type="Job description",
            role=self.cases.role,
            company=self.cases.company,
            timeline=self.cases.timeline,
            focus="4.1",
        )

        self.assertLess(
            document.index("Document details"),
            document.index('<article class="research-document'),
        )
        self.assertIn("<h1>Section 4. Mandatory Requirement</h1>", document)
        self.assertIn("<h2>4.1 Mandatory Certification</h2>", document)
        self.assertIn("20 July 2026", document)
        self.assertIn("27–30 August 2026", document)
        self.assertIn("20 September 2026", document)
        self.assertIn("research-document__focus", document)
        self.assertIn("Cited passage", document)

    def test_document_values_are_html_escaped(self) -> None:
        case = ParticipantCase(
            reference='<script>alert("candidate")</script>',
            sections=(
                CvSection(
                    id="cv_summary",
                    heading="Professional <Summary>",
                    text="Evidence & supporting detail.",
                ),
            ),
        )

        document = cv_document_html(
            case,
            role="AI <Lead>",
            company="Bank & Company",
            timeline=self.cases.timeline,
        )

        self.assertNotIn("<script>", document)
        self.assertIn("&lt;script&gt;", document)
        self.assertIn("Professional &lt;Summary&gt;", document)
        self.assertIn("Evidence &amp; supporting detail.", document)


if __name__ == "__main__":
    unittest.main()
