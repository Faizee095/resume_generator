from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from ._shared import (
    add_education,
    make_doc,
    plain_contact,
    section_heading,
    skill_groups,
    style,
)


TEMPLATE_ID = "timeline"
TEMPLATE_LABEL = "Timeline"
TEMPLATE_ORDER = 50

TEAL = "#126B67"
PALE = "#E8F3F2"
DARK = "#25343A"


def _timeline_job(story, job, width):
    date_style = style(
        "TimelineDate",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=1,
    )
    title_style = style(
        "TimelineTitle",
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=11,
        textColor=colors.HexColor(DARK),
    )
    company_style = style("TimelineCompany", fontSize=8.4, leading=10, textColor=colors.HexColor(TEAL))
    bullet_style = style("TimelineBullet", fontSize=8.5, leading=10.8, leftIndent=11)

    heading = Table(
        [[
            Paragraph(escape(job.get("dates", "")), date_style),
            [
                Paragraph(escape(job.get("title", "")), title_style),
                Paragraph(escape(job.get("company", "")), company_style),
            ],
        ]],
        colWidths=[1.12 * inch, width - 1.12 * inch],
        hAlign="LEFT",
    )
    heading.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor(TEAL)),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor(PALE)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, 0), 5),
        ("RIGHTPADDING", (0, 0), (0, 0), 5),
        ("LEFTPADDING", (1, 0), (1, 0), 8),
        ("RIGHTPADDING", (1, 0), (1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(heading)
    story.append(Spacer(1, 2))
    for item in job.get("bullets", []):
        story.append(Paragraph(f"- {escape(item)}", bullet_style))
    story.append(Spacer(1, 7))


def _skill_strip(skills, width):
    items = []
    groups = skill_groups(skills)
    for label, values in groups:
        if len(groups) > 1:
            items.append(f"{label}: {', '.join(values)}")
        else:
            items.extend(values)
    if not items:
        return Paragraph("No skills listed.", style("TimelineSkill"))
    cells = [
        Paragraph(escape(item), style("TimelineSkill", fontSize=7.8, leading=9.5, textColor=colors.HexColor(DARK)))
        for item in items
    ]
    rows = []
    for index in range(0, len(cells), 3):
        row = cells[index:index + 3]
        row.extend([""] * (3 - len(row)))
        rows.append(row)
    table = Table(rows, colWidths=[width / 3] * 3, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(PALE)),
        ("GRID", (0, 0), (-1, -1), 2, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def render_pdf(profile, education, resume, variant_id, output_path):
    doc, width = make_doc(output_path, margin=0.6, top=0.48, bottom=0.5)
    name_style = style("TimelineName", fontName="Helvetica-Bold", fontSize=21, leading=24, textColor=colors.HexColor(TEAL))
    headline_style = style("TimelineHeadline", fontName="Helvetica-Bold", fontSize=9, leading=11, textColor=colors.HexColor(DARK))
    contact_style = style("TimelineContact", fontSize=8, leading=10, textColor=colors.HexColor("#4E5B60"))
    story = [
        Paragraph(escape(profile.get("name", "")), name_style),
        Spacer(1, 2),
        Paragraph(escape(resume.get("headline", "")), headline_style),
        Spacer(1, 4),
        Paragraph(plain_contact(profile), contact_style),
        Spacer(1, 7),
    ]

    summary = resume.get("objective" if variant_id == "customer_relations" else "summary", "")
    summary_style = style("TimelineSummary", fontSize=8.8, leading=11.5)
    story.extend([
        section_heading("Objective" if variant_id == "customer_relations" else "Profile", width, TEAL),
        Spacer(1, 3),
        Paragraph(escape(summary), summary_style),
        Spacer(1, 7),
        section_heading("Core Strengths", width, TEAL),
        Spacer(1, 3),
        _skill_strip(resume.get("skills", []), width),
        Spacer(1, 8),
        section_heading("Career Timeline", width, TEAL),
        Spacer(1, 4),
    ])

    jobs = resume.get("experience", [])
    for job in jobs:
        _timeline_job(story, job, width)

    projects = resume.get("projects", [])
    if projects:
        story.extend([
            section_heading("Projects", width, TEAL),
            Spacer(1, 3),
        ])
        project_style = style("TimelineProject", fontSize=8.6, leading=11)
        for project in projects:
            story.extend([
                Paragraph(f"<b>{escape(project.get('title', ''))}</b>", project_style),
                Paragraph(escape(project.get("description", "")), project_style),
            ])
            story.extend(
                Paragraph(f"- {escape(item)}", project_style)
                for item in project.get("bullets", [])
            )
            story.append(Spacer(1, 4))

    story.extend([
        section_heading("Education", width, TEAL),
        Spacer(1, 3),
    ])
    add_education(story, education, width)

    achievements = resume.get("achievements", [])
    if achievements:
        achievement_style = style("TimelineAchievement", fontSize=8.5, leading=10.8, leftIndent=11)
        story.extend([
            Spacer(1, 6),
            section_heading("Highlights", width, TEAL),
            Spacer(1, 3),
        ])
        story.extend(
            Paragraph(f"- {escape(item)}", achievement_style)
            for item in achievements
        )

    doc.build(story)
