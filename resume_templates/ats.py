from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from ._shared import skill_groups


TEMPLATE_ID = "ats"
TEMPLATE_LABEL = "ATS-Friendly"
TEMPLATE_ORDER = 60


def _style(name, **kwargs):
    defaults = {
        "fontName": "Helvetica",
        "fontSize": 10,
        "textColor": colors.black,
        "leading": 13,
        "spaceBefore": 0,
        "spaceAfter": 0,
    }
    defaults.update(kwargs)
    return ParagraphStyle(name, **defaults)


def _contact_line(profile):
    parts = [
        profile.get("location", ""),
        profile.get("email", ""),
        profile.get("phone", ""),
    ]
    for link in profile.get("links", []):
        label = link.get("label", "")
        url = link.get("url", "")
        if label and url:
            parts.append(f"{label}: {url}")
    return " | ".join(escape(part) for part in parts if part)


def _section(story, title, section_style, gap=3):
    story.extend([
        Spacer(1, gap + 3),
        Paragraph(escape(title.upper()), section_style),
        Spacer(1, 2),
    ])


def render_pdf(profile, education, resume, variant_id, output_path):
    margin = 0.72 * inch
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=0.62 * inch,
        bottomMargin=0.62 * inch,
    )
    name_style = _style("ATSName", fontName="Helvetica-Bold", fontSize=18, leading=21)
    headline_style = _style("ATSHeadline", fontSize=10.5, leading=13)
    contact_style = _style("ATSContact", fontSize=9, leading=11)
    section_style = _style(
        "ATSSection",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        spaceBefore=5,
        borderPadding=0,
    )
    body_style = _style("ATSBody", fontSize=9.4, leading=12)
    bullet_style = _style("ATSBullet", fontSize=9.2, leading=11.5, leftIndent=12)
    entry_title_style = _style("ATSEntryTitle", fontName="Helvetica-Bold", fontSize=9.5, leading=12)

    story = [
        Paragraph(escape(profile.get("name", "")), name_style),
        Spacer(1, 2),
        Paragraph(escape(resume.get("headline", "")), headline_style),
        Spacer(1, 3),
        Paragraph(_contact_line(profile), contact_style),
    ]
    summary = resume.get("objective" if variant_id == "customer_relations" else "summary", "")
    _section(story, "Career Objective" if variant_id == "customer_relations" else "Professional Summary", section_style)
    story.append(Paragraph(escape(summary), body_style))

    _section(story, "Skills", section_style)
    groups = skill_groups(resume.get("skills", []))
    for label, items in groups:
        text = ", ".join(escape(item) for item in items)
        if len(groups) > 1:
            text = f"<b>{escape(label)}:</b> {text}"
        story.append(Paragraph(text, body_style))

    _section(story, "Professional Experience", section_style)
    for job in resume.get("experience", []):
        title_line = " | ".join(
            escape(value)
            for value in (job.get("title", ""), job.get("company", ""), job.get("dates", ""))
            if value
        )
        story.append(Paragraph(title_line, entry_title_style))
        for item in job.get("bullets", []):
            story.append(Paragraph(f"- {escape(item)}", bullet_style))
        story.append(Spacer(1, 3))

    projects = resume.get("projects", [])
    if projects:
        _section(story, "Projects", section_style)
        for project in projects:
            story.append(Paragraph(escape(project.get("title", "")), entry_title_style))
            if project.get("description"):
                story.append(Paragraph(escape(project["description"]), body_style))
            for item in project.get("bullets", []):
                story.append(Paragraph(f"- {escape(item)}", bullet_style))
            story.append(Spacer(1, 3))

    _section(story, "Education", section_style)
    for item in education:
        values = []
        for key in ("degree", "school", "year", "score"):
            if item.get(key):
                values.append(escape(item[key]))
        story.append(Paragraph(" | ".join(values), body_style))

    achievements = resume.get("achievements", [])
    if achievements:
        _section(story, "Achievements", section_style)
        for item in achievements:
            story.append(Paragraph(f"- {escape(item)}", bullet_style))

    doc.build(story)
