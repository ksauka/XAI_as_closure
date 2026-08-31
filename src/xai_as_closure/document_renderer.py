"""Shared, participant-facing document presentation for both studies."""

from __future__ import annotations

import html
import re
from pathlib import Path

from .cases import ParticipantCase, RecruitmentTimeline

_DOCUMENT_STYLES = """
<style>
.research-document-details {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(145px, 1fr));
    gap: 0.8rem;
    margin: 0.2rem 0 0.75rem;
    padding: 0.9rem 1rem;
    background: #f8f9fa;
    border: 1px solid #d9dee3;
    border-radius: 8px;
}
.research-document-details__heading {
    grid-column: 1 / -1;
    color: #343a40;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    line-height: 1.2;
    text-transform: uppercase;
}
.research-document-details__label {
    display: block;
    color: #68717b;
    font-size: 0.74rem;
    font-weight: 650;
    letter-spacing: 0.02em;
    margin-bottom: 0.16rem;
    text-transform: uppercase;
}
.research-document-details__value {
    color: #20252b;
    display: block;
    font-size: 0.94rem;
    font-weight: 600;
    line-height: 1.3;
}
.research-document {
    background: #ffffff;
    border: 1px solid #d9dee3;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(32, 37, 43, 0.07);
    color: #171717;
    font-family: "Times New Roman", Times, serif;
    font-size: 15px;
    line-height: 1.58;
    margin: 0 0 1rem;
    padding: 2rem 2.25rem 2.35rem;
}
.research-document * {
    font-family: "Times New Roman", Times, serif;
}
.research-document__type {
    color: #555;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.09em;
    margin: 0 0 0.35rem;
    text-transform: uppercase;
}
.research-document__title {
    border: 0;
    color: #111;
    font-size: 22px;
    font-weight: 700;
    line-height: 1.2;
    margin: 0;
    padding: 0;
}
.research-document__subtitle {
    color: #4b4b4b;
    font-size: 14px;
    margin: 0.45rem 0 0;
}
.research-document__rule {
    border: 0;
    border-top: 1px solid #b9b9b9;
    margin: 1rem 0 1.25rem;
}
.research-document section {
    margin: 0 0 1.15rem;
}
.research-document h1 {
    border-bottom: 1px solid #c8c8c8 !important;
    color: #111 !important;
    font-size: 16px !important;
    font-weight: 700 !important;
    letter-spacing: 0 !important;
    line-height: 1.25 !important;
    margin: 1.3rem 0 0.65rem !important;
    padding: 0 0 0.25rem !important;
}
.research-document h2 {
    border: 0 !important;
    color: #1f1f1f !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    letter-spacing: 0 !important;
    line-height: 1.35 !important;
    margin: 0.85rem 0 0.22rem !important;
    padding: 0 !important;
}
.research-document p {
    color: #171717;
    margin: 0.25rem 0 0.6rem;
}
.research-document ul {
    margin: 0.25rem 0 0.75rem 1.2rem;
    padding: 0;
}
.research-document li {
    margin: 0.16rem 0;
    padding-left: 0.12rem;
}
.research-document__subsection {
    border-left: 2px solid transparent;
    padding-left: 0.7rem;
}
.research-document__focus {
    background: #fff8dc;
    border-left-color: #c58a00;
    border-radius: 3px;
    margin: 0.55rem 0;
    padding: 0.35rem 0.7rem 0.45rem;
}
.research-document__focus-label {
    color: #745300;
    display: block;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.04em;
    margin-bottom: 0.1rem;
    text-transform: uppercase;
}
@media (max-width: 640px) {
    .research-document-details { grid-template-columns: 1fr; }
    .research-document { padding: 1.35rem 1.1rem 1.7rem; }
}
</style>
"""

_CITED_PASSAGE_ID = "cited-passage"


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _inline_markup(value: str) -> str:
    """Escape document text while retaining the limited authored emphasis."""
    escaped = _escape(value)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)


def _details_html(heading: str, fields: tuple[tuple[str, str], ...]) -> str:
    items = "".join(
        "<div>"
        f'<span class="research-document-details__label">{_escape(label)}</span>'
        f'<span class="research-document-details__value">{_escape(value)}</span>'
        "</div>"
        for label, value in fields
    )
    return (
        '<section class="research-document-details" aria-label="Document details">'
        f'<div class="research-document-details__heading">{_escape(heading)}</div>'
        f"{items}</section>"
    )


def _focus_label(focused: bool) -> str:
    if not focused:
        return ""
    return '<span class="research-document__focus-label">Cited passage</span>'


def _focus_attributes(focused: bool) -> str:
    """Give the one focused passage a stable, keyboard-focusable target."""
    if not focused:
        return ""
    return f' id="{_CITED_PASSAGE_ID}" tabindex="-1"'


def _paragraphs(text: str) -> str:
    return "".join(
        f"<p>{_inline_markup(paragraph.strip())}</p>"
        for paragraph in re.split(r"\n\s*\n", text)
        if paragraph.strip()
    )


def _education_html(text: str) -> str:
    parts: list[str] = []
    for paragraph in re.split(r"\n\s*\n", text):
        value = paragraph.strip()
        if not value:
            continue
        institution = re.fullmatch(r"\*\*(.+)\*\*", value)
        if institution:
            parts.append(f"<h2>{_escape(institution.group(1))}</h2>")
            continue
        labelled = re.fullmatch(r"(Degree|Core Competencies):\s*(.+)", value, re.DOTALL)
        if labelled:
            label, content = labelled.groups()
            parts.append(f"<p><em>{_escape(label)}</em>: {_inline_markup(content)}</p>")
            continue
        parts.append(f"<p>{_inline_markup(value)}</p>")
    return "".join(parts)


def _section_body(section_id: str, text: str) -> str:
    if section_id == "cv_education":
        return _education_html(text)
    lines = [line.removeprefix("- ").strip() for line in text.splitlines()]
    if lines and all(
        line.startswith("- ") for line in text.splitlines() if line.strip()
    ):
        items = "".join(f"<li>{_inline_markup(line)}</li>" for line in lines if line)
        return f"<ul>{items}</ul>"
    return _paragraphs(text)


def cv_document_html(
    case: ParticipantCase,
    *,
    role: str,
    company: str,
    timeline: RecruitmentTimeline,
    focus: str = "",
) -> str:
    """Build a readable, anonymised CV without exposing internal section IDs."""
    details = _details_html(
        "Candidate details",
        (
            ("Candidate reference", case.reference),
            ("Position", role),
            ("Organisation", company),
            ("Screening window", timeline.screening_window_label),
        ),
    )
    content: list[str] = [
        '<article class="research-document research-document--cv">',
        '<div class="research-document__type">Curriculum Vitae</div>',
        f'<div class="research-document__title">Candidate {_escape(case.reference)}</div>',
        '<hr class="research-document__rule">',
    ]
    index = 0
    while index < len(case.sections):
        section = case.sections[index]
        role_match = re.fullmatch(r"cv_role_(\d+)", section.id)
        if role_match:
            content.append('<section class="research-document__section">')
            content.append("<h1>Experience</h1>")
            while index < len(case.sections):
                role_section = case.sections[index]
                role_match = re.fullmatch(r"cv_role_(\d+)", role_section.id)
                if not role_match:
                    break
                focused = focus == f"3.{role_match.group(1)}"
                classes = "research-document__subsection"
                if focused:
                    classes += " research-document__focus"
                content.extend(
                    (
                        f'<div class="{classes}"{_focus_attributes(focused)}>',
                        _focus_label(focused),
                        f"<h2>{_escape(role_section.heading)}</h2>",
                        _paragraphs(role_section.text),
                        "</div>",
                    )
                )
                index += 1
            content.append("</section>")
            continue

        section_number = {
            "cv_summary": "1",
            "cv_education": "2",
            "cv_certifications": "4",
            "cv_skills": "5",
            "cv_memberships": "6",
            "cv_hobbies": "7",
        }.get(section.id, "")
        focused = bool(section_number and focus == section_number)
        classes = "research-document__section"
        if focused:
            classes += " research-document__focus"
        content.extend(
            (
                f'<section class="{classes}"{_focus_attributes(focused)}>',
                _focus_label(focused),
                f"<h1>{_escape(section.heading)}</h1>",
                _section_body(section.id, section.text),
                "</section>",
            )
        )
        index += 1
    content.append("</article>")
    return details + "".join(content)


def _reference_sections(markdown: str, focus: str) -> tuple[str, str, str]:
    title = "Reference document"
    subtitle = ""
    body: list[str] = []
    open_section = False
    clause_pattern = re.compile(r"^\*\*(\d+\.\d+)\s+([^*]+?)\.\*\*\s*(.*)$")
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("# "):
            title = line.removeprefix("# ").strip()
            continue
        if line.startswith("*(") and line.endswith(")*"):
            subtitle = line[2:-2]
            continue
        if line.startswith("## "):
            if open_section:
                body.append("</section>")
            body.extend(
                (
                    '<section class="research-document__section">',
                    f"<h1>{_escape(line.removeprefix('## ').strip())}</h1>",
                )
            )
            open_section = True
            continue
        clause = clause_pattern.fullmatch(line)
        if clause:
            number, clause_title, clause_text = clause.groups()
            focused = focus == number
            classes = "research-document__subsection"
            if focused:
                classes += " research-document__focus"
            body.extend(
                (
                    f'<div class="{classes}"{_focus_attributes(focused)}>',
                    _focus_label(focused),
                    f"<h2>{_escape(number)} {_escape(clause_title)}</h2>",
                    f"<p>{_inline_markup(clause_text)}</p>",
                    "</div>",
                )
            )
            continue
        body.append(f"<p>{_inline_markup(line)}</p>")
    if open_section:
        body.append("</section>")
    return title, subtitle, "".join(body)


def reference_document_html(
    markdown: str,
    *,
    document_type: str,
    role: str,
    company: str,
    timeline: RecruitmentTimeline,
    focus: str = "",
) -> str:
    """Build a paper-like job-description or recruitment-policy document."""
    title, subtitle, body = _reference_sections(markdown, focus)
    timeline_fields = (
        ("Posted", timeline.posted_label),
        ("Screening window", timeline.screening_window_label),
        ("Target fill", timeline.target_fill_label),
    )
    details = _details_html(
        "Document details",
        (
            ("Document", document_type),
            ("Position", role),
            ("Organisation", company),
            *timeline_fields,
        ),
    )
    subtitle_html = (
        f'<p class="research-document__subtitle"><em>{_escape(subtitle)}</em></p>'
        if subtitle
        else ""
    )
    article = (
        '<article class="research-document research-document--reference">'
        f'<div class="research-document__type">{_escape(document_type)}</div>'
        f'<div class="research-document__title">{_escape(title)}</div>'
        f'{subtitle_html}<hr class="research-document__rule">{body}</article>'
    )
    return details + article


def citation_document_frame_html(document: str) -> str:
    """Wrap a complete safe document and scroll its cited passage into view."""
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"{_DOCUMENT_STYLES}"
        "<style>body{margin:0;padding:.35rem;background:#f4f5f7;}"
        ".research-document-details{background:#fff;}"
        ".research-document{box-shadow:none;margin-bottom:.35rem;}</style>"
        f"</head><body><main>{document}</main>"
        "<script>window.addEventListener('load',()=>{requestAnimationFrame(()=>{"
        f"const target=document.getElementById('{_CITED_PASSAGE_ID}');"
        "if(target){target.focus({preventScroll:true});"
        "target.scrollIntoView({block:'center',inline:'nearest'});}});});</script>"
        "</body></html>"
    )


def render_cv_document(
    st,
    case: ParticipantCase,
    *,
    role: str,
    company: str,
    timeline: RecruitmentTimeline,
    focus: str = "",
) -> None:
    """Render candidate details followed by a complete CV paper."""
    st.markdown(_DOCUMENT_STYLES, unsafe_allow_html=True)
    st.markdown(
        cv_document_html(
            case,
            role=role,
            company=company,
            timeline=timeline,
            focus=focus,
        ),
        unsafe_allow_html=True,
    )


def render_reference_document(
    st,
    path: Path,
    *,
    document_type: str,
    role: str,
    company: str,
    timeline: RecruitmentTimeline,
    focus: str = "",
) -> None:
    """Render one complete authored knowledge document as a paper."""
    st.markdown(_DOCUMENT_STYLES, unsafe_allow_html=True)
    st.markdown(
        reference_document_html(
            path.read_text(encoding="utf-8"),
            document_type=document_type,
            role=role,
            company=company,
            timeline=timeline,
            focus=focus,
        ),
        unsafe_allow_html=True,
    )


__all__ = [
    "citation_document_frame_html",
    "cv_document_html",
    "reference_document_html",
    "render_cv_document",
    "render_reference_document",
]
