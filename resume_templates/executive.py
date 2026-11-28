from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from ._shared import (
    add_education,
    add_experience,
    make_doc,
    photo_flowable,
    section_heading,
    skill_groups,
    style,
)


TEMPLATE_ID = "executive"
TEMPLATE_LABEL = "Executive"
TEMPLATE_ORDER = 40

NAVY = "#17304F"
BLUE = "#2D5F91"
GOLD = "#D2A85A"
PALE = "#EFF3F7"


def _skills_table(skills, width):
    cards = []
    for label, items in skill_groups(skills):
        value = ", ".join(escape(item) for item in items)
        cards.append((
            Paragraph(
                escape(label),
                style("SkillCardLabel", fontName="Helvetica-Bold", fontSize=8.2, textColor=colors.HexColor(BLUE)),
            ),
            Paragraph(value, style("SkillCardText", fontSize=8.2, leading=10.4)),
        ))

    if not cards:
        return Paragraph("No skills listed.", style("SkillCardText", fontSize=8.2))

    rows = []
    for index in range(0, len(cards), 2):
        cells = []
        for card in cards[index:index + 2]:
            cell = Table([[card[0]], [card[1]]], colWidths=[width * 0.46])
            cell.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(PALE)),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            cells.append(cell)
        if len(cells) == 1:
            cells.append("")
        rows.append(cells)

    table = Table(rows, colWidths=[width * 0.5, width * 0.5], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def render_pdf(profile, education, resume, variant_id, output_path):
    doc, width = make_doc(output_path, margin=0.62, top=0.42, bottom=0.48)
    white = colors.white
    header_name = style(
        "ExecutiveName",
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=25,
        textColor=white,
    )
    header_headline = style(
        "ExecutiveHeadline",
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor("#E3EAF2"),
    )
    header_contact = style(
        "ExecutiveContact",
        fontSize=8,
        leading=10,
        textColor=white,
    )
    name = Paragraph(escape(profile.get("name", "")), header_name)
    headline = Paragraph(escape(resume.get("headline", "")), header_headline)
    from resume_templates._shared import plain_contact

    contact = Paragraph(plain_contact(profile), header_contact)
    header_content = [name, Spacer(1, 4), headline, Spacer(1, 6), contact]
    photo = photo_flowable(profile, width=0.92, height=1.1)
    if photo:
        header_cells = [[photo, header_content]]
        header_widths = [1.05 * inch, width - 1.05 * inch]
    else:
        header_cells = [[header_content]]
        header_widths = [width]
    header = Table(header_cells, colWidths=header_widths, hAlign="LEFT")
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(NAVY)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 11),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
    ]))

    story = [header, Spacer(1, 9)]
    objective_label = "Objective" if variant_id == "customer_relations" else "Executive Summary"
    story.append(section_heading(objective_label, width, GOLD, background=NAVY))
    body = style("ExecutiveSummary", fontSize=9, leading=12)
    summary = resume.get("objective" if variant_id == "customer_relations" else "summary", "")
    story.extend([Spacer(1, 4), Paragraph(escape(summary), body), Spacer(1, 7)])

    story.append(section_heading("Expertise", width, GOLD, background=NAVY))
    story.extend([Spacer(1, 3), _skills_table(resume.get("skills", []), width)])

    story.extend([
        Spacer(1, 7),
        section_heading("Experience", width, GOLD, background=NAVY),
        Spacer(1, 4),
    ])
    add_experience(story, resume, width, BLUE)

    projects = resume.get("projects", [])
    if projects:
        story.extend([
            Spacer(1, 7),
            section_heading("Selected Projects", width, GOLD, background=NAVY),
            Spacer(1, 3),
        ])
        project_title = style("ExecutiveProjectTitle", fontName="Helvetica-Bold", fontSize=9, textColor=colors.HexColor(BLUE))
        project_body = style("ExecutiveProjectBody", fontSize=8.5, leading=11)
        for project in projects:
            block = [
                Paragraph(escape(project.get("title", "")), project_title),
                Paragraph(escape(project.get("description", "")), project_body),
            ]
            block.extend(
                Paragraph(f"- {escape(item)}", project_body)
                for item in project.get("bullets", [])
            )
            story.append(KeepTogether(block[:2]))
            story.extend(block[2:])
            story.append(Spacer(1, 3))

    story.extend([
        Spacer(1, 7),
        section_heading("Education", width, GOLD, background=NAVY),
        Spacer(1, 3),
    ])
    add_education(story, education, width)

    achievements = resume.get("achievements", [])
    if achievements:
        story.extend([
            Spacer(1, 7),
            section_heading("Key Achievements", width, GOLD, background=NAVY),
            Spacer(1, 3),
        ])
        achievement_style = style("ExecutiveAchievement", fontSize=8.7, leading=11.2, leftIndent=11)
        story.extend(
            Paragraph(f"- {escape(item)}", achievement_style)
            for item in achievements
        )

    doc.build(story)
