import base64
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def style(name, **kwargs):
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


def make_doc(output_path, margin=0.62, top=0.5, bottom=0.48):
    margin_size = margin * inch
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=margin_size,
        rightMargin=margin_size,
        topMargin=top * inch,
        bottomMargin=bottom * inch,
    )
    return doc, letter[0] - 2 * margin_size


def photo_flowable(profile, width=0.9, height=1.08):
    photo_base64 = profile.get("photo_base64", "")
    if photo_base64:
        encoded = photo_base64.split(",", 1)[1] if "," in photo_base64 else photo_base64
        source = BytesIO(base64.b64decode(encoded))
    else:
        photo_path = profile.get("photo_path", "")
        if not photo_path:
            return None
        resolved = Path(photo_path)
        if not resolved.is_absolute():
            resolved = Path(__file__).resolve().parents[1] / resolved
        if not resolved.exists():
            return None
        source = str(resolved)
    return Image(source, width=width * inch, height=height * inch, kind="proportional")


def plain_contact(profile, include_urls=False):
    parts = [
        profile.get("location", ""),
        profile.get("email", ""),
        profile.get("phone", ""),
    ]
    for link in profile.get("links", []):
        label = link.get("label", "")
        url = link.get("url", "")
        if label and url:
            parts.append(f"{label}: {url}" if include_urls else label)
    return "  |  ".join(escape(part) for part in parts if part)


def section_heading(title, width, accent, background=None):
    text_color = colors.white if background else colors.HexColor(accent)
    paragraph = Paragraph(
        escape(title.upper()),
        style("SectionHeading", fontName="Helvetica-Bold", fontSize=9.2, textColor=text_color),
    )
    table = Table([[paragraph]], colWidths=[width], hAlign="LEFT")
    if background:
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(background)),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
    else:
        table.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 0.8, colors.HexColor(accent)),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
    return table


def skill_groups(skills):
    if skills and isinstance(skills[0], str):
        return [("Skills", skills)]
    return [
        (skill.get("label", ""), skill.get("items", []))
        for skill in skills
    ]


def add_experience(story, resume, width, accent, compact=False):
    title_style = style(
        "ExperienceTitle",
        fontName="Helvetica-Bold",
        fontSize=9 if compact else 10,
        textColor=colors.HexColor(accent),
        leading=11,
    )
    company_style = style("ExperienceCompany", fontSize=8.5, textColor=colors.HexColor("#59616B"))
    date_style = style("ExperienceDate", fontSize=8.1, textColor=colors.HexColor("#59616B"), alignment=2)
    bullet_style = style("ExperienceBullet", fontSize=8.2 if compact else 8.8, leading=10.4 if compact else 11.5, leftIndent=11)
    for index, job in enumerate(resume.get("experience", [])):
        header = Table(
            [[
                Paragraph(escape(job.get("title", "")), title_style),
                Paragraph(escape(job.get("dates", "")), date_style),
            ]],
            colWidths=[width * 0.68, width * 0.32],
            hAlign="LEFT",
        )
        header.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(header)
        story.append(Paragraph(escape(job.get("company", "")), company_style))
        for item in job.get("bullets", []):
            story.append(Paragraph(f"- {escape(item)}", bullet_style))
        if index < len(resume.get("experience", [])) - 1:
            story.append(Spacer(1, 4))


def add_education(story, education, width):
    body = style("EducationBody", fontSize=8.7, leading=11)
    date_style = style("EducationDate", fontSize=8.1, textColor=colors.HexColor("#59616B"), alignment=2)
    for item in education:
        if item.get("school"):
            text = "<br/>".join(
                escape(value)
                for value in (item.get("school", ""), item.get("degree", ""), item.get("score", ""))
                if value
            )
        else:
            text = escape(item.get("degree", ""))
        row = Table(
            [[Paragraph(text, body), Paragraph(escape(item.get("year", "")), date_style)]],
            colWidths=[width * 0.78, width * 0.22],
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
