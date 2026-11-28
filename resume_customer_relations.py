import base64
import os
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
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

from resume_data import contact_line, load_resume, output_path


PROFILE, EDUCATION, RESUME = load_resume("customer_relations")
OUTPUT = str(output_path(RESUME))
TEMPLATE_ID = os.environ.get("RESUME_TEMPLATE_ID", "classic")
if TEMPLATE_ID != "classic":
    from resume_layouts import generate_alternative_pdf

    generate_alternative_pdf(
        PROFILE,
        EDUCATION,
        RESUME,
        "customer_relations",
        TEMPLATE_ID,
        OUTPUT,
    )
    print("Done:", OUTPUT)
    raise SystemExit(0)


doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=letter,
    leftMargin=0.42 * inch,
    rightMargin=0.42 * inch,
    topMargin=0.30 * inch,
    bottomMargin=0.35 * inch,
)

PAGE_W = letter[0] - 0.84 * inch
BLACK = colors.HexColor("#111111")
GRAY = colors.HexColor("#555555")
DIVIDER = colors.HexColor("#777777")


def style(name, **kwargs):
    defaults = dict(
        fontName="Helvetica",
        fontSize=9,
        textColor=BLACK,
        leading=11,
        spaceBefore=0,
        spaceAfter=0,
    )
    defaults.update(kwargs)
    return ParagraphStyle(name, **defaults)


S_NAME = style("Name", fontSize=18, fontName="Helvetica-Bold", alignment=TA_LEFT, leading=21)
S_CONTACT = style("Contact", fontSize=8.5, textColor=BLACK, alignment=TA_LEFT, leading=11)
S_SECTION = style("Section", fontSize=10, fontName="Helvetica-Bold", leading=12)
S_BODY = style("Body", fontSize=8.5, leading=10.5)
S_EXPERIENCE_TITLE = style("ExperienceTitle", fontSize=9.2, fontName="Helvetica-Bold", leading=11)
S_DATE = style("Date", fontSize=8.2, textColor=GRAY, alignment=TA_RIGHT, leading=10)
S_EDUCATION = style("Education", fontSize=8.7, leading=10)
S_BULLET = style("Bullet", fontSize=8.5, leftIndent=12, leading=10.5)


def bullet_list(items, bullet="•"):
    return [Paragraph(f"{bullet} {item}", S_BULLET) for item in items]


def section_header(title):
    table = Table([[Paragraph(title, S_SECTION)]], colWidths=[PAGE_W], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.8, DIVIDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return table


def load_profile_photo(profile):
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
    if resolved.exists():
        return str(resolved)
    return None


story = []

photo = load_profile_photo(PROFILE)
header_right = [
    Paragraph(PROFILE["name"], S_NAME),
    Spacer(1, 5),
    Paragraph(contact_line(PROFILE), S_CONTACT),
]

header_cells = []
if photo:
    profile_image = Image(photo, width=1.15 * inch, height=1.38 * inch)
    profile_image.hAlign = "LEFT"
    header_cells.append(profile_image)
else:
    header_cells.append("")
header_cells.append(header_right)

header = Table([header_cells], colWidths=[1.28 * inch, PAGE_W - 1.28 * inch], hAlign="LEFT")
header.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ("TOPPADDING", (0, 0), (-1, -1), 0),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
]))
story.append(header)

story.append(section_header("Objective"))
story.append(Spacer(1, 3))
story.append(Paragraph(RESUME["objective"], S_BODY))

story.append(Spacer(1, 8))
story.append(section_header("Experience"))
story.append(Spacer(1, 4))

for index, job in enumerate(RESUME.get("experience", [])):
    title_left = Paragraph(job["company"], S_EXPERIENCE_TITLE)
    job_title = Paragraph(job["title"], S_EXPERIENCE_TITLE)
    dates = Paragraph(job["dates"], S_DATE)

    top = Table([[title_left, dates]], colWidths=[PAGE_W * 0.68, PAGE_W * 0.32], hAlign="LEFT")
    top.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    content = [top, job_title]
    content.extend(bullet_list(job.get("bullets", [])))
    story.append(KeepTogether(content))
    if index < len(RESUME.get("experience", [])) - 1:
        story.append(Spacer(1, 4))

story.append(Spacer(1, 8))
story.append(section_header("Education"))
story.append(Spacer(1, 4))

for index, education in enumerate(EDUCATION):
    school = education["school"]
    degree = education["degree"]
    year = education["year"]
    score = education.get("score", "")
    left = Paragraph(f"• {school}<br/><font size='8.5'>{degree}<br/>{score}</font>", S_EDUCATION)
    right = Paragraph(year, S_DATE)
    row = Table([[left, right]], colWidths=[PAGE_W * 0.82, PAGE_W * 0.18], hAlign="LEFT")
    row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(row)

story.append(Spacer(1, 6))
story.append(section_header("Skills"))
story.append(Spacer(1, 3))
for index, skill in enumerate(RESUME.get("skills", []), start=1):
    story.append(Paragraph(f"• {index}. {skill}" if False else f"• {skill}", S_BULLET))

story.append(Spacer(1, 7))
story.append(section_header("Achievements"))
story.append(Spacer(1, 3))
story.extend(bullet_list(RESUME.get("achievements", [])))


doc.build(story)
print("Done:", OUTPUT)
