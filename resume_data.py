import json
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr


PROJECT_DIR = Path(__file__).resolve().parent


def load_resume(variant_id):
    data = json.loads((PROJECT_DIR / "resume_data.json").read_text(encoding="utf-8"))
    profile = data["profile"]
    education = data["education"]
    variant = data["variants"][variant_id]

    required_fields = ("label", "output_name", "headline", "summary", "skills", "experience", "projects")
    missing_fields = [field for field in required_fields if field not in variant]
    if missing_fields:
        raise ValueError(f"Resume variant {variant_id!r} is missing: {', '.join(missing_fields)}")

    return profile, education, variant


def output_path(variant):
    today = datetime.now()
    day_suffix = "th" if 10 < today.day % 100 < 14 else {
        1: "st",
        2: "nd",
        3: "rd",
    }.get(today.day % 10, "th")
    date_label = f"{today.day}{day_suffix}{today.strftime('%B%Y')}"
    return PROJECT_DIR / f"{variant['output_name']}_{date_label}.pdf"


def contact_line(profile):
    items = [escape(profile[key]) for key in ("location", "email", "phone")]
    items.extend(
        f"<link href={quoteattr(link['url'])} color=\"#2563eb\">{escape(link['label'])}</link>"
        for link in profile["links"]
    )
    return "  |  ".join(items)


def project_subtitle(project):
    parts = []
    if project.get("organization"):
        parts.append(project["organization"])

    role = project.get("role", "")
    team = project.get("team", "")
    if role and team:
        role = f"{role} ({team})"
    elif not role:
        role = team
    if role:
        parts.append(role)

    if project.get("technologies"):
        parts.append(", ".join(project["technologies"]))
    if project.get("context"):
        parts.append(project["context"])

    return "  ·  ".join(parts)
