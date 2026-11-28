import base64
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from resume_data import contact_line


LAYOUTS = {
    "modern": {
        "label": "Modern",
        "accent": "#2457A7",
        "light": "#EAF0F8",
        "margin": 0.62,
        "name_alignment": TA_LEFT,
        "name_font": "Helvetica-Bold",
        "name_size": 22,
        "section_style": "filled",
    },
    "elegant": {
        "label": "Elegant",
        "accent": "#7A4E2D",
        "light": "#F5EFE9",
        "margin": 0.68,
        "name_alignment": TA_CENTER,
        "name_font": "Times-Bold",
        "name_size": 23,
        "section_style": "rule",
    },
    "compact": {
        "label": "Compact",
        "accent": "#176B66",
        "light": "#E8F2F1",
        "margin": 0.48,
        "name_alignment": TA_LEFT,
        "name_font": "Helvetica-Bold",
        "name_size": 17,
        "section_style": "compact",
    },
}


def _style(name, **kwargs):
    defaults = {
        "fontName": "Helvetica",
        "fontSize": 8.8,
        "textColor": colors.HexColor("#20242A"),
        "leading": 11.5,
        "spaceBefore": 0,
        "spaceAfter": 0,
    }
    defaults.update(kwargs)
    return ParagraphStyle(name, **defaults)


def _profile_photo(profile):
    photo_base64 = profile.get("photo_base64", "")
    if photo_base64:
        encoded = photo_base64.split(",", 1)[1] if "," in photo_base64 else photo_base64
        return BytesIO(base64.b64decode(encoded))

    photo_path = profile.get("photo_path", "")
    if not photo_path:
        return None
    resolved = Path(photo_path)
    if not resolved.is_absolute():
        resolved = Path(__file__).resolve().parent / resolved
    return str(resolved) if resolved.exists() else None


def _section_header(title, page_width, config):
    accent = colors.HexColor(config["accent"])
    light = colors.HexColor(config["light"])
    label = Paragraph(
        escape(title.upper()),
        _style("Section", fontName="Helvetica-Bold", fontSize=9.2, textColor=accent),
    )
    table = Table([[label]], colWidths=[page_width], hAlign="LEFT")
    if config["section_style"] == "filled":
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), light),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
    elif config["section_style"] == "compact":
        table.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 1.1, accent),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
    else:
        table.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 0.7, accent),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
    return table


def _skill_flowables(skills, page_width, config, body_style):
    accent = colors.HexColor(config["accent"])
    if skills and isinstance(skills[0], str):
        skill_texts = [escape(skill) for skill in skills if skill]
        if config["section_style"] == "compact":
            rows = []
            for index in range(0, len(skill_texts), 2):
                rows.append([
                    Paragraph(f"- {skill_texts[index]}", body_style),
                    Paragraph(f"- {skill_texts[index + 1]}", body_style)
                    if index + 1 < len(skill_texts) else "",
                ])
            table = Table(rows, colWidths=[page_width * 0.5, page_width * 0.5], hAlign="LEFT")
            table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]))
            return [table]
        return [Paragraph(f"- {skill}", body_style) for skill in skill_texts]

    flowables = []
    label_style = _style("SkillLabel", fontName="Helvetica-Bold", textColor=accent)
    for skill in skills:
        label = escape(skill.get("label", ""))
        items = ", ".join(escape(item) for item in skill.get("items", []))
        row = Table(
            [[Paragraph(f"{label}:", label_style), Paragraph(items, body_style)]],
            colWidths=[1.05 * inch, page_width - 1.05 * inch],
            hAlign="LEFT",
        )
        row.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        flowables.append(row)
    return flowables


def generate_alternative_pdf(profile, education, resume, variant_id, layout_id, output_path):
    config = LAYOUTS[layout_id]
    margin = config["margin"] * inch
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=0.52 * inch,
        bottomMargin=0.48 * inch,
    )
    page_width = letter[0] - 2 * margin
    accent = colors.HexColor(config["accent"])
    compact = config["section_style"] == "compact"
    body_style = _style("Body", fontSize=8.2 if compact else 8.8, leading=10.4 if compact else 11.5)
    title_style = _style(
        "EntryTitle",
        fontName="Helvetica-Bold",
        fontSize=9.2 if compact else 10,
        textColor=accent,
        leading=11,
    )
    company_style = _style("Company", fontSize=8.5, textColor=colors.HexColor("#59616B"))
    date_style = _style("Date", fontSize=8.1, textColor=colors.HexColor("#59616B"), alignment=TA_RIGHT)
    bullet_style = _style("Bullet", fontSize=body_style.fontSize, leading=body_style.leading, leftIndent=11)
    name_style = _style(
        "Name",
        fontName=config["name_font"],
        fontSize=config["name_size"],
        leading=config["name_size"] + 3,
        textColor=accent,
        alignment=config["name_alignment"],
    )
    headline_style = _style(
        "Headline",
        fontSize=9.2,
        textColor=colors.HexColor("#414A55"),
        alignment=config["name_alignment"],
        leading=12,
    )
    contact_style = _style(
        "Contact",
        fontSize=8.1,
        textColor=colors.HexColor("#414A55"),
        alignment=config["name_alignment"],
        leading=10,
    )
    story = []
    photo = _profile_photo(profile)
    if photo and config["name_alignment"] == TA_LEFT:
        image = Image(photo, width=0.92 * inch, height=1.1 * inch, kind="proportional")
        header_content = [
            Paragraph(escape(profile.get("name", "")), name_style),
            Spacer(1, 3),
            Paragraph(escape(resume.get("headline", "")), headline_style),
            Spacer(1, 4),
            Paragraph(contact_line(profile), contact_style),
        ]
        header = Table(
            [[image, header_content]],
            colWidths=[1.03 * inch, page_width - 1.03 * inch],
            hAlign="LEFT",
        )
        header.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(header)
    else:
        story.extend([
            Paragraph(escape(profile.get("name", "")), name_style),
            Spacer(1, 2),
            Paragraph(escape(resume.get("headline", "")), headline_style),
            Spacer(1, 4),
            Paragraph(contact_line(profile), contact_style),
        ])
        if photo:
            image = Image(photo, width=0.86 * inch, height=1.02 * inch, kind="proportional")
            image.hAlign = "CENTER"
            story.extend([Spacer(1, 4), image])

    story.extend([
        Spacer(1, 7),
        _section_header("Objective" if variant_id == "customer_relations" else "Summary", page_width, config),
        Spacer(1, 3),
        Paragraph(escape(resume.get("objective" if variant_id == "customer_relations" else "summary", "")), body_style),
        Spacer(1, 6),
        _section_header("Skills", page_width, config),
        Spacer(1, 3),
    ])
    story.extend(_skill_flowables(resume.get("skills", []), page_width, config, body_style))

    story.extend([
        Spacer(1, 6),
        _section_header("Experience", page_width, config),
        Spacer(1, 3),
    ])
    jobs = resume.get("experience", [])
    for index, job in enumerate(jobs):
        header = Table(
            [[
                Paragraph(escape(job.get("title", "")), title_style),
                Paragraph(escape(job.get("dates", "")), date_style),
            ]],
            colWidths=[page_width * 0.68, page_width * 0.32],
            hAlign="LEFT",
        )
        header.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        content = [header, Paragraph(escape(job.get("company", "")), company_style)]
        content.extend(Paragraph(f"- {escape(item)}", bullet_style) for item in job.get("bullets", []))
        story.append(KeepTogether(content))
        if index < len(jobs) - 1:
            story.append(Spacer(1, 4))

    projects = resume.get("projects", [])
    if projects:
        story.extend([
            Spacer(1, 6),
            _section_header("Projects", page_width, config),
            Spacer(1, 3),
        ])
        for project in projects:
            content = [
                Paragraph(escape(project.get("title", "")), title_style),
                Paragraph(escape(project.get("description", "")), body_style),
            ]
            content.extend(Paragraph(f"- {escape(item)}", bullet_style) for item in project.get("bullets", []))
            story.append(KeepTogether(content[:2]))
            story.extend(content[2:])
            story.append(Spacer(1, 3))

    story.extend([
        Spacer(1, 6),
        _section_header("Education", page_width, config),
        Spacer(1, 3),
    ])
    for item in education:
        if "school" in item:
            left_text = "<br/>".join(
                escape(value) for value in (item.get("school", ""), item.get("degree", ""), item.get("score", "")) if value
            )
        else:
            left_text = escape(item.get("degree", ""))
        row = Table(
            [[Paragraph(left_text, body_style), Paragraph(escape(item.get("year", "")), date_style)]],
            colWidths=[page_width * 0.78, page_width * 0.22],
            hAlign="LEFT",
        )
        row.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(row)

    achievements = resume.get("achievements", [])
    if achievements:
        story.extend([
            Spacer(1, 6),
            _section_header("Achievements", page_width, config),
            Spacer(1, 3),
        ])
        story.extend(Paragraph(f"- {escape(item)}", bullet_style) for item in achievements)

    doc.build(story)
