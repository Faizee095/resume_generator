from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

today = datetime.now()
day_suffix = "th" if 10 < today.day % 100 < 14 else {1: "st", 2: "nd", 3: "rd"}.get(today.day % 10, "th")
date_label = f"{today.day}{day_suffix}{today.strftime('%B%Y')}"
OUTPUT = f"E:\\Personal\\Projects\\resume_generator\\Faiyazuddin_Fullstack Developer_{date_label}.pdf"

doc = SimpleDocTemplate(
    OUTPUT,
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
    defaults = dict(fontName="Helvetica", fontSize=9, textColor=BLACK,
                    leading=13, spaceBefore=0, spaceAfter=0)
    defaults.update(kwargs)
    return ParagraphStyle(name, **defaults)


S_NAME = style("Name", fontSize=16, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=20, spaceAfter=2)
S_CONTACT = style("Contact", fontSize=8.0, textColor=GRAY, alignment=TA_CENTER)
S_HEADLINE = style("Headline", fontSize=9.2, fontName="Helvetica-Bold", textColor=GRAY, alignment=TA_CENTER, leading=12, spaceAfter=2)
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
    return HRFlowable(width="100%", thickness=0.5, color=DIVIDER,
                      spaceBefore=before, spaceAfter=after)


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
    return [Paragraph(f"• {item}", S_BULLET) for item in items]


story = []

# Header
story.append(Paragraph("Md Faiyazuddin Siddique", S_NAME))
story.append(Paragraph(
    "Full Stack Developer  |  Node.js  |  Express  |  React  |  TypeScript  |  REST APIs",
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
    "Full Stack Developer with 5+ years of experience delivering production web applications across frontend and backend, "
    "with primary expertise in React, TypeScript, and frontend architecture. Hands-on backend experience with Node.js, "
    "Express, REST and GraphQL APIs, JWT authentication, session workflows, and AI/report-generation orchestration. "
    "Experienced in leading migrations, mentoring developers, and delivering maintainable end-to-end systems.",
    S_SUMMARY,
))

# Skills
story.append(divider())
story.append(section_header("SKILLS"))
skills = [
    ("Backend", "Node.js, Express.js, REST API Design, GraphQL, API Orchestration"),
    ("Auth", "JWT Authentication, Authorization, Session Management, Token Handling"),
    ("Frontend", "React.js, TypeScript, Next.js, Redux, TanStack Query"),
    ("UI", "Tailwind CSS, Material-UI (MUI), Responsive Design, Accessibility (a11y)"),
    ("Engineering", "Reusable Components, Performance Optimization, Testing (Jest), Git"),
    ("Data", "Charting Libraries, Table Libraries, Excel Data Workflows"),
    ("Tools", "Jira, Figma, Auth0, Firebase, Supabase"),
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
    ("Software Engineer | Full Stack", "SourceFuse", "Feb 2025 – Jun 2026", [
        "Led frontend architecture for AI-driven applications using React and TypeScript, enabling scalable production systems",
        "Designed reusable component systems to improve consistency and speed of feature development",
        "Led frontend modernization from legacy systems to React-based architecture across multiple projects",
        "Established frontend best practices, architectural guidelines, and collaboration patterns for production delivery",
        "Contributed to Node.js and Express services supporting request handling, authentication, and session workflows",
        "Worked with backend API integrations and authentication/session flows to support secure application experiences",
    ]),
    ("Career Break", "Personal / Family Responsibilities", "Oct 2024 – Jan 2025", [
        "Took a planned career break to manage family responsibilities before returning to software engineering",
    ]),
    ("Software Engineer | Full Stack", "Kfaqs Infotech Pvt Ltd", "Feb 2022 – Sep 2024", [
        "Built and maintained 5+ production web applications using React and Redux",
        "Improved application performance through lazy loading, code splitting, and frontend optimization techniques",
        "Strengthened application stability through proactive debugging and issue resolution",
        "Implemented and integrated REST and GraphQL APIs across multiple production applications",
        "Contributed to backend request handling and API workflows alongside frontend feature development",
    ]),
    ("Associate Software Engineer | Full Stack", "TCS", "Jan 2021 – Feb 2022", [
        "Contributed to React-based frontend modules and API-connected user workflows",
        "Built XML/XSL-based validation systems supporting high-volume banking workflows",
        "Automated recurring banking workflow tasks using scripts and APIs, contributing to end-to-end processing",
    ]),
]
for index, (title, company, duration, job_bullets) in enumerate(jobs):
    story.extend(job_header(title, company, duration))
    story.extend(bullets(job_bullets))
    if index < len(jobs) - 1:
        story.append(Spacer(1, 3))

# Projects
projects = [
    ("AI Chat Platform", "Rakuten  ·  Full Stack Developer / Frontend Lead (1 junior developer)  ·  Node.js, Express, React, TypeScript, Tailwind CSS, TanStack Query, GraphQL", "Led frontend development and independently implemented backend features for an AI-powered reporting platform that converts user requests into structured reports and visual outputs.", [
        "Designed response-driven React components that render tables, charts, SQL results, and PDF newsletters based on backend responses",
        "Built a real-time session sidebar supporting creation, renaming, deletion, and switching between chat/report sessions",
        "Implemented the frontend using React, TypeScript, Tailwind CSS, and TanStack Query",
        "Built backend APIs to receive user queries and orchestrate the AI and report-generation workflow",
        "Implemented chat/report session APIs plus JWT authentication, authorization, token handling, and session management",
    ]),
    ("Topia Web App", "Full Stack Developer / Frontend Lead (team of 3, including 2 junior developers)  ·  Node.js, Express, React, TypeScript, Redux, Tailwind CSS, TanStack Query, REST APIs", "Led the migration of a complex enterprise application from .NET to React while coordinating with full-stack developers migrating backend services to Java.", [
        "Managed a frontend team of three developers and coordinated implementation across interconnected application modules",
        "Decomposed the legacy application into independently deliverable React components and defined an incremental migration architecture",
        "Implemented and integrated API workflows for migrated modules using REST services and TanStack Query",
        "Coordinated authentication and authorization changes across frontend and backend API migration work",
    ]),
    ("Nuvama Web App", "Full Stack Developer / Frontend Lead (1 junior developer)  ·  React, TypeScript, Material-UI, Redux, GraphQL", "Led the migration of a complex .NET web application to React while contributing to API-connected workflows, analyzing legacy architecture, mapping interconnected components, and defining an incremental delivery plan.", [
        "Worked with one junior developer, providing technical guidance and training throughout the migration",
        "Owned frontend migration planning, ticket breakdown, and sprint execution across component areas",
        "Rebuilt legacy workflows and implemented GraphQL-connected features using React, Material-UI, and Redux while maintaining consistent user experiences",
        "Contributed to backend API integration and request/response workflows for migrated application modules",
        "Established reusable component patterns and frontend implementation standards for the migrated application",
    ]),
    ("Carbon Emission Tracker", "Full Stack Developer  ·  Node.js, Express, React, TypeScript, GraphQL", "Built an enterprise carbon accounting platform for calculating emissions from vehicles, machines, factories, and other operational sources against regulatory thresholds.", [
        "Developed interactive dashboards with charts, visualizations, and tables for categorized emission data",
        "Implemented Excel upload and categorization workflows for industry-specific data",
        "Added Jest component tests and accessibility improvements as part of frontend delivery standards",
        "Implemented backend APIs for emission data workflows, report requests, and long-running report-generation processes",
        "Supported real-time report progress updates using GraphQL subscriptions",
    ]),
]
for index, (title, subtitle, description, project_bullets) in enumerate(projects):
    project_header = [
        Paragraph(title, S_JOBTITLE),
        Paragraph(subtitle, S_COMPANY),
        Paragraph(description, S_PROJDESC),
    ]
    project_bullet_flowables = bullets(project_bullets)
    if index == 0:
        project_header = [divider(), section_header("PROJECTS"), *project_header]
    story.append(KeepTogether(project_header + project_bullet_flowables[:1]))
    story.extend(project_bullet_flowables[1:])
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
