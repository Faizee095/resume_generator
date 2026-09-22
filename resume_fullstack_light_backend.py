from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


PROJECT_DIR = Path(__file__).resolve().parent
today = datetime.now()
day_suffix = "th" if 10 < today.day % 100 < 14 else {
    1: "st",
    2: "nd",
    3: "rd",
}.get(today.day % 10, "th")
date_label = f"{today.day}{day_suffix}{today.strftime('%B%Y')}"
OUTPUT = PROJECT_DIR / f"Faiyazuddin_Fullstack Light Backend_{date_label}.pdf"


doc = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=letter,
    leftMargin=0.60 * inch,
    rightMargin=0.60 * inch,
    topMargin=0.45 * inch,
    bottomMargin=0.45 * inch,
)

PAGE_W = letter[0] - 1.20 * inch
BLACK = colors.HexColor("#1a1a1a")
GRAY = colors.HexColor("#444444")
LIGHT_GRAY = colors.HexColor("#888888")
DIVIDER = colors.HexColor("#cccccc")


def style(name, **kwargs):
    defaults = dict(
        fontName="Helvetica",
        fontSize=9,
        textColor=BLACK,
        leading=13,
        spaceBefore=0,
        spaceAfter=0,
    )
    defaults.update(kwargs)
    return ParagraphStyle(name, **defaults)


S_NAME = style("Name", fontSize=16, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=20, spaceAfter=2)
S_CONTACT = style("Contact", fontSize=8.0, textColor=GRAY, alignment=TA_CENTER)
S_HEADLINE = style(
    "Headline",
    fontSize=9.2,
    fontName="Helvetica-Bold",
    textColor=GRAY,
    alignment=TA_CENTER,
    leading=12,
    spaceAfter=2,
)
S_SECTION = style("Section", fontSize=8.8, fontName="Helvetica-Bold")
S_JOBTITLE = style("JobTitle", fontSize=9.2, fontName="Helvetica-Bold")
S_COMPANY = style("Company", fontSize=8.8, textColor=GRAY, spaceAfter=1)
S_DATE = style("Date", fontSize=8.2, textColor=LIGHT_GRAY, alignment=TA_RIGHT)
S_BULLET = style("Bullet", fontSize=8.5, leftIndent=12, leading=11.5)
S_SUMMARY = style("Summary", fontSize=8.5, leading=12)
S_SKILL_L = style("SkillL", fontSize=8.5, fontName="Helvetica-Bold")
S_SKILL_V = style("SkillV", fontSize=8.5, textColor=GRAY)
S_PROJDESC = style("ProjDesc", fontSize=8.5, leading=11.5, spaceAfter=1)


def divider(before=3, after=2):
    return HRFlowable(
        width="100%",
        thickness=0.5,
        color=DIVIDER,
        spaceBefore=before,
        spaceAfter=after,
    )


def section_header(text):
    table = Table([[Paragraph(text, S_SECTION)]], colWidths=[PAGE_W], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return table


def job_header(title, company, duration):
    table = Table(
        [[Paragraph(title, S_JOBTITLE), Paragraph(duration, S_DATE)]],
        colWidths=[PAGE_W * 0.68, PAGE_W * 0.32],
        hAlign="LEFT",
    )
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return [table, Paragraph(company, S_COMPANY)]


def bullets(items):
    return [Paragraph(f"- {item}", S_BULLET) for item in items]


story = []

# Header
story.append(Paragraph("Md Faiyazuddin Siddique", S_NAME))
story.append(Paragraph(
    "Full Stack Developer  |  React  |  TypeScript  |  Node.js  |  REST APIs  |  Auth and Sessions",
    S_HEADLINE,
))
story.append(Paragraph(
    'Muzaffarpur, India  |  faiyazsiddique9@gmail.com  |  +91-8709442967  '
    '|  <link href="https://faiyazuddin.netlify.app/" color="#2563eb">Portfolio</link>  '
    '|  <link href="https://www.linkedin.com/in/md-faiyazuddin-siddique-244a73192/" color="#2563eb">LinkedIn</link>  '
    '|  <link href="https://github.com/Faizee095" color="#2563eb">GitHub</link>',
    S_CONTACT,
))
story.append(HRFlowable(width="100%", thickness=1, color=BLACK, spaceBefore=6, spaceAfter=0))

# Summary
story.append(section_header("SUMMARY"))
story.append(Paragraph(
    "Software Engineer with 5+ years of experience building production web applications, primarily with React and TypeScript. "
    "Hands-on backend development experience with REST and GraphQL APIs, CRUD workflows, request handling, authentication, "
    "authorization, and session management. Comfortable working across the stack to build backend features and connect user workflows "
    "to reliable APIs.",
    S_SUMMARY,
))

# Skills
story.append(divider())
story.append(section_header("SKILLS"))
skills = [
    ("Backend", "Node.js, Express.js, REST APIs, GraphQL, Request Handling, API Integration"),
    ("Data Workflows", "CRUD Operations, Validation, Report Requests, File Uploads, SQL Result Handling"),
    ("Auth", "JWT Authentication, Authorization, Token Handling, Session Management"),
    ("Frontend", "React.js, TypeScript, Next.js, Redux, TanStack Query"),
    ("Data and Tools", "Firebase, Supabase, MongoDB, MySQL, Git, Jira, Figma"),
    ("Quality", "Debugging, Jest, Accessibility, Performance Optimization, Code Review"),
]
for label, value in skills:
    row = Table(
        [[Paragraph(label + ":", S_SKILL_L), Paragraph(value, S_SKILL_V)]],
        colWidths=[1.05 * inch, PAGE_W - 1.05 * inch],
        hAlign="LEFT",
    )
    row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    story.append(row)

# Experience
story.append(divider())
story.append(section_header("EXPERIENCE"))
jobs = [
    ("Software Engineer", "SourceFuse", "Feb 2025 - Jun 2026", [
        "Led frontend development for AI-driven applications using React and TypeScript",
        "Designed reusable component systems and frontend patterns for scalable production delivery",
        "Built API-connected workflows for data fetching, report generation, user actions, and structured AI responses",
        "Developed selected Node.js and Express features for request handling, authentication, and session workflows",
        "Improved authentication and session experiences by reducing redundant requests and clarifying client-side state handling",
    ]),
    ("Career Break", "Personal / Family Responsibilities", "Oct 2024 - Jan 2025", [
        "Took a planned career break to manage family responsibilities before returning to software engineering",
    ]),
    ("Software Engineer", "Kfaqs Infotech Pvt Ltd", "Feb 2022 - Sep 2024", [
        "Built and maintained production web applications using React, Redux, and reusable frontend patterns",
        "Improved application performance through frontend optimization and reliable user workflows",
        "Integrated REST and GraphQL APIs across multiple application workflows",
        "Implemented backend features for selected CRUD workflows, request handling, validation, and issue resolution",
    ]),
    ("Associate Software Engineer", "TCS", "Jan 2021 - Feb 2022", [
        "Contributed to React modules and API-connected user workflows",
        "Built XML/XSL-based validation interfaces and systems for high-volume banking workflows",
        "Automated recurring banking workflow tasks using scripts and APIs",
    ]),
]
for index, (title, company, duration, job_bullets) in enumerate(jobs):
    story.extend(job_header(title, company, duration))
    story.extend(bullets(job_bullets))
    if index < len(jobs) - 1:
        story.append(Spacer(1, 3))

# Projects
story.append(divider())
story.append(section_header("SELECTED PROJECTS"))
projects = [
    (
        "AI Chat Platform",
        "Rakuten  |  React, TypeScript, Node.js, Express, GraphQL",
        "AI-powered reporting platform that turns user requests into structured reports, charts, SQL results, and PDF newsletters.",
        [
            "Led frontend development for chat, report generation, tables, charts, SQL results, and newsletter outputs",
            "Designed response-driven React components that render different result types from backend responses",
            "Implemented session interfaces for creating, renaming, deleting, and switching between chat and report sessions",
            "Developed supporting APIs and implemented JWT authentication, authorization, and session workflows",
        ],
    ),
    (
        "Topia Web App",
        "Enterprise application  |  React, TypeScript, Node.js, Express, REST APIs",
        "Incremental migration of a complex enterprise application from .NET to React while backend services moved to Java.",
        [
            "Led the frontend migration of interconnected enterprise workflows from .NET to React",
            "Decomposed legacy screens into reusable components and implemented CRUD-style user workflows",
            "Integrated REST APIs and coordinated request/response behavior with backend developers",
            "Implemented frontend authentication and authorization flows during the backend service migration",
        ],
    ),
    (
        "Nuvama Web App",
        "Enterprise application  |  React, TypeScript, Material-UI, Redux, GraphQL",
        "Migration of a complex .NET web application to React with API-connected workflows and coordinated backend feature delivery.",
        [
            "Led the frontend migration of legacy workflows using React, Redux, and Material-UI",
            "Recreated interconnected screens and maintained consistent user experiences across the migration",
            "Integrated GraphQL workflows and established reusable component and API-consumption patterns",
            "Contributed to authentication and authorization changes across frontend and backend boundaries",
        ],
    ),
    (
        "Carbon Emission Tracker",
        "Enterprise dashboard  |  React, TypeScript, Node.js, Express, GraphQL",
        "Carbon accounting platform for calculating emissions from vehicles, machines, factories, and other operational sources.",
        [
            "Built interactive dashboards with charts, data visualizations, and tables for categorized emission data",
            "Implemented data-entry, categorization, and Excel upload workflows for enterprise users",
            "Connected GraphQL queries and subscriptions to long-running report generation and real-time progress updates",
        ],
    ),
]
for index, (title, subtitle, description, project_bullets) in enumerate(projects):
    project_content = [
        Paragraph(title, S_JOBTITLE),
        Paragraph(subtitle, S_COMPANY),
        Paragraph(description, S_PROJDESC),
        *bullets(project_bullets),
    ]
    story.append(KeepTogether(project_content))
    if index < len(projects) - 1:
        story.append(Spacer(1, 3))

# Education
story.append(divider())
story.append(section_header("EDUCATION"))
education = Table(
    [[Paragraph("B.Tech in Computer Science", S_JOBTITLE), Paragraph("2020", S_DATE)]],
    colWidths=[PAGE_W * 0.68, PAGE_W * 0.32],
    hAlign="LEFT",
)
education.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ("TOPPADDING", (0, 0), (-1, -1), 0),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
]))
story.append(education)

doc.build(story)
print("Done:", OUTPUT)
