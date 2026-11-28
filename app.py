import copy
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

from resume_data import PROJECT_DIR
from resume_templates import template_options
from resume_library import (
    delete_resume,
    get_pdf_download,
    get_saved_resume,
    list_pdf_history,
    list_saved_resumes,
    record_pdf_download as store_pdf_download,
    save_resume,
)


load_dotenv(PROJECT_DIR / ".env")

DATA_PATH = PROJECT_DIR / "resume_data.json"
TEMPLATE_DATA_PATH = PROJECT_DIR / "resume_template.json"
SAHIL_DATA_PATH = PROJECT_DIR / "sahil_resume.json"
CUSTOM_DATA_PATH = PROJECT_DIR / "resume_custom.json"
IS_RENDER = os.environ.get("RENDER", "").strip().lower() == "true" or bool(
    os.environ.get("RENDER_EXTERNAL_URL", "").strip()
)
PERSISTENCE_MODE = "supabase" if IS_RENDER else os.environ.get("PERSISTENCE_MODE", "local").strip().lower()
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "").strip().lower()
SAHIL_EMAIL = os.environ.get("SAHIL_EMAIL", "sahil@resume.com").strip().lower()
SCRIPT_BY_VARIANT = {
    "frontend": "resume_frontend.py",
    "fullstack": "resume_fullstack.py",
    "fullstack_frontend_lead": "resume_fullstack_light_backend.py",
    "customer_relations": "resume_customer_relations.py",
}
PDF_LAYOUTS = template_options()
ADD_LABELS = {
    "Links": "Add link",
    "Education entries": "Add education entry",
    "Skill groups": "Add skill group",
    "Experience entries": "Add experience entry",
    "Projects": "Add project",
}

st.set_page_config(page_title="Resume Workshop", layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] { background: #f5f6f2; }
    [data-testid="stSidebar"] { background: #e9eee9; }
    [data-testid="stHeader"] { background: rgba(245, 246, 242, 0.92); }
    div[data-testid="stMetric"] { background: #ffffff; border: 1px solid #dfe5df; padding: 12px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def read_default_data():
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def read_user_template(email=None):
    template = json.loads(TEMPLATE_DATA_PATH.read_text(encoding="utf-8"))
    normalized_email = (email or "").strip().lower()
    if normalized_email == SAHIL_EMAIL:
        sahil = json.loads(SAHIL_DATA_PATH.read_text(encoding="utf-8"))
        template["profile"] = copy.deepcopy(sahil["profile"])
        template["education"] = copy.deepcopy(sahil["education"])
        template["variants"]["customer_relations"] = copy.deepcopy(
            sahil["variants"]["customer_relations"]
        )
    return template


def user_role(email):
    if PERSISTENCE_MODE != "supabase" or email.strip().lower() == ADMIN_EMAIL:
        return "admin"
    return "user"


def saved_resume_signature(data, name, variant_id):
    return json.dumps({
        "data": json.loads(data_signature(data)),
        "name": name,
        "variant_id": variant_id,
    }, ensure_ascii=False, sort_keys=True)


def get_supabase_client():
    if "supabase_client" not in st.session_state:
        st.session_state["supabase_client"] = create_client(SUPABASE_URL, SUPABASE_KEY)
    return st.session_state["supabase_client"]


def show_login():
    st.title("Resume Workshop")

    login_tab, signup_tab = st.tabs(["Sign in", "Create account"])

    with login_tab:
        with st.form("supabase-login"):
            email = st.text_input("Email", key="login-email")
            password = st.text_input("Password", type="password", key="login-password")
            submitted = st.form_submit_button("Sign in", type="primary")

        if submitted:
            normalized_email = email.strip().lower()
            try:
                client = get_supabase_client()
                response = client.auth.sign_in_with_password({
                    "email": normalized_email,
                    "password": password,
                })
                if response.user is None:
                    raise ValueError("Supabase did not return an authenticated user.")
                st.session_state["supabase_user_id"] = response.user.id
                st.session_state["supabase_user_email"] = response.user.email or normalized_email
                st.session_state["supabase_user_role"] = user_role(st.session_state["supabase_user_email"])
                st.rerun()
            except Exception:
                st.error("Sign-in failed. Check the credentials and confirm the email account.")

    with signup_tab:
        with st.form("supabase-signup"):
            signup_email = st.text_input("Email", key="signup-email")
            signup_password = st.text_input("Password", type="password", key="signup-password")
            signup_confirm = st.text_input("Confirm password", type="password", key="signup-confirm")
            signup_submitted = st.form_submit_button("Create account", type="primary")

        if signup_submitted:
            normalized_email = signup_email.strip().lower()
            if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized_email):
                st.error("Enter a valid email address.")
            elif len(signup_password) < 8:
                st.error("Password must be at least 8 characters.")
            elif signup_password != signup_confirm:
                st.error("Passwords do not match.")
            else:
                try:
                    response = get_supabase_client().auth.sign_up({
                        "email": normalized_email,
                        "password": signup_password,
                    })
                    if response.user is not None:
                        if response.session is None:
                            st.success("Account created. Check your email and confirm the account before signing in.")
                        else:
                            st.session_state["supabase_user_id"] = response.user.id
                            st.session_state["supabase_user_email"] = response.user.email or normalized_email
                            st.session_state["supabase_user_role"] = user_role(st.session_state["supabase_user_email"])
                            st.rerun()
                    else:
                        st.error("The account could not be created.")
                except Exception:
                    st.error("Sign-up failed. The email may already be registered or confirmation may be disabled.")


def attach_editor_ids(data):
    collections = [data["profile"]["links"], data["education"]]
    for variant in data["variants"].values():
        collections.extend((variant["skills"], variant["experience"], variant["projects"]))
    for collection in collections:
        for item in collection:
            if isinstance(item, dict):
                item.setdefault("_editor_id", uuid.uuid4().hex)
    return data


def clean_editor_ids(value):
    if isinstance(value, dict):
        return {
            key: clean_editor_ids(item)
            for key, item in value.items()
            if not key.startswith("_editor_")
        }
    if isinstance(value, list):
        return [clean_editor_ids(item) for item in value]
    return value


def editor_key(key):
    revision = st.session_state.get("draft_revision", 0)
    return f"draft-{revision}-{key}"


def edit_text(record, field, label, key, multiline=False, height=100, help_text=None):
    value = record.get(field, "")
    if isinstance(value, list):
        value = "\n".join(str(item) for item in value)
    value = str(value or "")

    if multiline:
        updated = st.text_area(label, value=value, key=editor_key(key), height=height, help=help_text)
    else:
        updated = st.text_input(label, value=value, key=editor_key(key), help=help_text)
    record[field] = updated
    return updated


def edit_lines(record, field, label, key, height=110):
    value = edit_text(
        record,
        field,
        label,
        key,
        multiline=True,
        height=height,
        help_text="Enter one item per line.",
    )
    record[field] = [line.strip() for line in value.splitlines() if line.strip()]


def render_collection(items, title, key_prefix, new_item, draw_item, display_name):
    for index, item in enumerate(items):
        heading = display_name(item) or f"New {title[:-1].lower()}"
        with st.expander(f"{index + 1:02d}  {heading}", expanded=False):
            draw_item(item, f"{key_prefix}-{item['_editor_id']}")
            controls = st.columns([1, 1, 1, 5])
            if controls[0].button(
                "Move up",
                icon=":material/arrow_upward:",
                key=editor_key(f"{key_prefix}-{item['_editor_id']}-up"),
                disabled=index == 0,
            ):
                items[index - 1], items[index] = items[index], items[index - 1]
                st.rerun()
            if controls[1].button(
                "Move down",
                icon=":material/arrow_downward:",
                key=editor_key(f"{key_prefix}-{item['_editor_id']}-down"),
                disabled=index == len(items) - 1,
            ):
                items[index + 1], items[index] = items[index], items[index + 1]
                st.rerun()
            if controls[2].button(
                "Remove",
                icon=":material/delete:",
                key=editor_key(f"{key_prefix}-{item['_editor_id']}-remove"),
            ):
                items.pop(index)
                st.rerun()

    if st.button(ADD_LABELS[title], icon=":material/add:", key=editor_key(f"{key_prefix}-add")):
        item = new_item()
        item["_editor_id"] = uuid.uuid4().hex
        items.append(item)
        st.rerun()


def draw_link(link, key):
    left, right = st.columns(2)
    with left:
        edit_text(link, "label", "Link label", f"{key}-label")
    with right:
        edit_text(link, "url", "URL", f"{key}-url")


def draw_education(item, key):
    if "school" in item:
        school_column, degree_column = st.columns(2)
        with school_column:
            edit_text(item, "school", "School or college", f"{key}-school")
            edit_text(item, "degree", "Qualification", f"{key}-degree")
        with degree_column:
            edit_text(item, "year", "Year", f"{key}-year")
            edit_text(item, "score", "Score or grade", f"{key}-score")
    else:
        left, right = st.columns([3, 1])
        with left:
            edit_text(item, "degree", "Degree or qualification", f"{key}-degree")
        with right:
            edit_text(item, "year", "Year", f"{key}-year")


def draw_skill(skill, key):
    edit_text(skill, "label", "Skill group name", f"{key}-label")
    edit_lines(skill, "items", "Skills", f"{key}-items", height=125)


def draw_experience(job, key):
    left, right = st.columns([2, 1])
    with left:
        edit_text(job, "title", "Job title", f"{key}-title")
        edit_text(job, "company", "Company", f"{key}-company")
    with right:
        edit_text(job, "dates", "Dates", f"{key}-dates")
    edit_lines(job, "bullets", "Responsibilities and achievements", f"{key}-bullets", height=150)


def draw_project(project, key):
    edit_text(project, "title", "Project name", f"{key}-title")
    left, right = st.columns(2)
    with left:
        edit_text(project, "organization", "Organization", f"{key}-organization")
        edit_text(project, "role", "Your role", f"{key}-role")
    with right:
        edit_text(project, "team", "Team size or direct reports", f"{key}-team")
        edit_text(project, "context", "Context label (optional)", f"{key}-context")
    edit_lines(project, "technologies", "Technologies", f"{key}-technologies", height=90)
    edit_text(project, "description", "Project description", f"{key}-description", multiline=True, height=105)
    edit_lines(project, "bullets", "Your contributions", f"{key}-bullets", height=150)


def validate_resume(data, variant_id):
    issues = []
    profile = data["profile"]
    variant = data["variants"][variant_id]

    if not profile.get("name", "").strip():
        issues.append("Add your name in Contact details.")
    if "@" not in profile.get("email", ""):
        issues.append("Enter a valid email address in Contact details.")
    if not variant.get("headline", "").strip():
        issues.append("Add a headline.")
    if variant_id == "customer_relations":
        if not variant.get("objective", "").strip():
            issues.append("Add an objective.")
        if not variant.get("skills"):
            issues.append("Add at least one skill.")
        if not variant.get("achievements"):
            issues.append("Add at least one achievement.")
    elif not variant.get("summary", "").strip():
        issues.append("Add a summary.")
    if not re.fullmatch(r"[A-Za-z0-9 _-]+", variant.get("output_name", "")):
        issues.append("Use only letters, numbers, spaces, underscores, or hyphens in the PDF filename prefix.")
    if not data.get("education"):
        issues.append("Add at least one education entry.")
    if not variant.get("skills"):
        issues.append("Add at least one skill group.")
    if not variant.get("experience"):
        issues.append("Add at least one experience entry.")
    if variant_id != "customer_relations" and not variant.get("projects"):
        issues.append("Add at least one project.")

    for index, link in enumerate(profile.get("links", []), start=1):
        if bool(link.get("label")) != bool(link.get("url")):
            issues.append(f"Contact link {index}: provide both a label and URL, or clear both fields.")
        elif link.get("url") and not link["url"].startswith(("https://", "http://")):
            issues.append(f"Contact link {index}: URL must start with http:// or https://.")

    for index, job in enumerate(variant.get("experience", []), start=1):
        if not job.get("title", "").strip() or not job.get("company", "").strip():
            issues.append(f"Experience {index}: add both a job title and company.")
        if variant_id != "customer_relations" and not any(line.strip() for line in job.get("bullets", [])):
            issues.append(f"Experience {index}: add at least one bullet.")

    if variant_id != "customer_relations":
        for index, project in enumerate(variant.get("projects", []), start=1):
            if not project.get("title", "").strip() or not project.get("description", "").strip():
                issues.append(f"Project {index}: add a name and description.")
            if not any(line.strip() for line in project.get("bullets", [])):
                issues.append(f"Project {index}: add at least one contribution.")

    return issues


def data_signature(data):
    return json.dumps(clean_editor_ids(data), ensure_ascii=False, sort_keys=True)


def validate_draft_structure(data, defaults):
    if not isinstance(data, dict) or data.get("schema_version") != defaults.get("schema_version"):
        raise ValueError("The saved draft has an unsupported data schema.")
    if not isinstance(data.get("profile"), dict) or not isinstance(data["profile"].get("links"), list):
        raise ValueError("The saved draft has invalid profile or link data.")
    if not isinstance(data.get("education"), list):
        raise ValueError("The saved draft has invalid education data.")
    if not isinstance(data.get("variants"), dict) or set(data["variants"]) != set(defaults["variants"]):
        raise ValueError("The saved draft does not contain the expected resume variants.")

    for variant_id, variant in data["variants"].items():
        fields = ("skills", "experience", "projects")
        if variant_id == "customer_relations":
            fields = ("skills", "experience", "achievements")
        for field in fields:
            if not isinstance(variant.get(field), list):
                raise ValueError(f"The saved {variant_id} draft has invalid {field} data.")


def load_custom_draft(defaults):
    if PERSISTENCE_MODE == "supabase":
        return attach_editor_ids(copy.deepcopy(defaults)), None, None

    if not CUSTOM_DATA_PATH.exists():
        return attach_editor_ids(copy.deepcopy(defaults)), None, None

    try:
        saved_data = json.loads(CUSTOM_DATA_PATH.read_text(encoding="utf-8"))
        validate_draft_structure(saved_data, defaults)
        return attach_editor_ids(saved_data), data_signature(saved_data), None
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        message = f"Could not load {CUSTOM_DATA_PATH.name}: {error} Default data loaded; the saved file was left untouched."
        return attach_editor_ids(copy.deepcopy(defaults)), None, message


def read_local_custom_draft(defaults):
    saved_data = json.loads(CUSTOM_DATA_PATH.read_text(encoding="utf-8"))
    validate_draft_structure(saved_data, defaults)
    return attach_editor_ids(saved_data)


def save_custom_draft(data, defaults):
    clean_data = clean_editor_ids(data)
    validate_draft_structure(clean_data, defaults)
    if PERSISTENCE_MODE == "supabase":
        get_supabase_client().table("resume_drafts").upsert(
            {
                "user_id": st.session_state["supabase_user_id"],
                "data": clean_data,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            on_conflict="user_id",
        ).execute()
        return

    temporary_file = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix=".resume_custom_",
            suffix=".tmp",
            dir=PROJECT_DIR,
            delete=False,
        ) as file:
            temporary_file = Path(file.name)
            json.dump(clean_data, file, ensure_ascii=False, indent=2)
        os.replace(temporary_file, CUSTOM_DATA_PATH)
    except OSError:
        if temporary_file and temporary_file.exists():
            temporary_file.unlink()
        raise


def generate_pdf(variant_id, resume_data, layout_id="classic"):
    clean_data = clean_editor_ids(resume_data)
    with tempfile.TemporaryDirectory(prefix="resume-workshop-") as temporary_directory:
        temporary_path = Path(temporary_directory)
        custom_data_path = temporary_path / "resume_data.json"
        custom_data_path.write_text(json.dumps(clean_data, ensure_ascii=False), encoding="utf-8")

        environment = os.environ.copy()
        environment["RESUME_DATA_PATH"] = str(custom_data_path)
        environment["RESUME_OUTPUT_DIR"] = str(temporary_path)
        environment["RESUME_TEMPLATE_ID"] = layout_id
        script_path = PROJECT_DIR / SCRIPT_BY_VARIANT[variant_id]
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_DIR,
            env=environment,
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
        if result.returncode:
            message = result.stderr.strip() or result.stdout.strip() or "PDF generation failed."
            raise RuntimeError(message)

        generated_pdfs = list(temporary_path.glob("*.pdf"))
        if len(generated_pdfs) != 1:
            raise RuntimeError("The generator did not produce exactly one PDF.")
        pdf_path = generated_pdfs[0]
        filename = pdf_path.name
        if layout_id != "classic":
            filename = f"{pdf_path.stem}_{layout_id}{pdf_path.suffix}"
        return filename, pdf_path.read_bytes()


def record_download_request(user_id, artifact):
    if PERSISTENCE_MODE != "supabase":
        return
    try:
        store_pdf_download(
            get_supabase_client(),
            user_id,
            artifact["content"],
            artifact["filename"],
            artifact["resume_name"],
            artifact["variant_id"],
            artifact.get("saved_resume_id"),
        )
        st.session_state["pdf_history_notice"] = f"{artifact['filename']} added to PDF downloads."
        st.session_state.pop("pdf_history_error", None)
    except Exception:
        st.session_state["pdf_history_error"] = "The PDF downloaded, but it could not be added to history."


def render_download(variant_id, signature, layout_id):
    artifact = st.session_state.get("generated_artifact")
    if not artifact:
        return
    if (
        artifact["variant_id"] != variant_id
        or artifact["signature"] != signature
        or artifact.get("layout_id") != layout_id
    ):
        return
    st.download_button(
        "Download PDF",
        data=artifact["content"],
        file_name=artifact["filename"],
        mime="application/pdf",
        icon=":material/download:",
        key="download-current-resume",
        on_click=record_download_request if PERSISTENCE_MODE == "supabase" else None,
        args=(st.session_state["supabase_user_id"], artifact) if PERSISTENCE_MODE == "supabase" else None,
    )
    history_notice = st.session_state.pop("pdf_history_notice", None)
    history_error = st.session_state.pop("pdf_history_error", None)
    if history_notice:
        st.success(history_notice)
    if history_error:
        st.warning(history_error)


def render_generate_button(
    variant_id,
    payload,
    signature,
    label,
    layout_id="classic",
    resume_name=None,
    saved_resume_id=None,
):
    if st.button(label, type="primary", icon=":material/picture_as_pdf:", key=f"generate-{label}"):
        issues = validate_resume(payload, variant_id)
        if issues:
            st.session_state["generation_issues"] = issues
            st.session_state.pop("generated_artifact", None)
        else:
            st.session_state.pop("generation_issues", None)
            try:
                with st.spinner("Building PDF..."):
                    filename, content = generate_pdf(variant_id, payload, layout_id)
                st.session_state["generated_artifact"] = {
                    "variant_id": variant_id,
                    "signature": signature,
                    "layout_id": layout_id,
                    "filename": filename,
                    "content": content,
                    "resume_name": resume_name or payload["variants"][variant_id]["label"],
                    "saved_resume_id": saved_resume_id,
                }
            except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
                st.session_state.pop("generated_artifact", None)
                st.error(f"Could not generate the PDF: {error}")

    for issue in st.session_state.get("generation_issues", []):
        st.error(issue)
    render_download(variant_id, signature, layout_id)


def new_record(**fields):
    fields["_editor_id"] = uuid.uuid4().hex
    return fields


def open_saved_resume(resume_id):
    try:
        record = get_saved_resume(
            get_supabase_client(),
            st.session_state["supabase_user_id"],
            resume_id,
        )
        validate_draft_structure(record["data"], st.session_state["default_data"])
        st.session_state["draft_data"] = attach_editor_ids(record["data"])
        st.session_state["active_saved_resume_id"] = record["id"]
        st.session_state["active_saved_resume_name"] = record["name"]
        st.session_state["saved_draft_signature"] = saved_resume_signature(
            record["data"], record["name"], record["variant_id"]
        )
        st.session_state["draft_load_error"] = None
        st.session_state["resume-variant"] = st.session_state["default_data"]["variants"][record["variant_id"]]["label"]
        st.session_state["workspace-mode"] = "Customize"
        st.session_state["draft_revision"] += 1
        st.session_state.pop("generated_artifact", None)
        st.session_state.pop("generation_issues", None)
        st.session_state.pop("library_error", None)
    except Exception as error:
        st.session_state["library_error"] = f"Could not open saved resume: {error}"


def prepare_saved_resume_pdf(record, layout_id):
    issues = validate_resume(record["data"], record["variant_id"])
    if issues:
        st.error("This saved resume needs attention before generating a PDF: " + " ".join(issues))
        return
    try:
        with st.spinner("Building PDF..."):
            filename, content = generate_pdf(record["variant_id"], record["data"], layout_id)
        st.session_state["generated_artifact"] = {
            "variant_id": record["variant_id"],
            "signature": data_signature(record["data"]),
            "layout_id": layout_id,
            "filename": filename,
            "content": content,
            "resume_name": record["name"],
            "saved_resume_id": record["id"],
        }
        st.session_state.pop("generation_issues", None)
    except Exception as error:
        st.error(f"Could not generate the PDF: {error}")


if PERSISTENCE_MODE not in {"local", "supabase"}:
    st.error("PERSISTENCE_MODE must be either 'local' or 'supabase'.")
    st.stop()

if PERSISTENCE_MODE == "supabase":
    missing_settings = [
        name for name, value in (
            ("SUPABASE_URL", SUPABASE_URL),
            ("SUPABASE_KEY", SUPABASE_KEY),
            ("ADMIN_EMAIL", ADMIN_EMAIL),
        ) if not value
    ]
    if missing_settings:
        st.error(f"Missing required Supabase settings: {', '.join(missing_settings)}")
        st.stop()
    if "supabase_user_id" not in st.session_state or "supabase_client" not in st.session_state:
        show_login()
        st.stop()

if PERSISTENCE_MODE == "supabase":
    current_role = user_role(st.session_state.get("supabase_user_email", ""))
    if st.session_state.get("supabase_user_role") != current_role:
        role_scoped_keys = {
            "default_data",
            "draft_data",
            "saved_draft_signature",
            "draft_load_error",
            "draft_revision",
            "active_saved_resume_id",
            "active_saved_resume_name",
            "generated_artifact",
            "history_pdf_artifact",
            "generation_issues",
        }
        for key in list(st.session_state):
            if key.startswith("draft-") or key in role_scoped_keys:
                st.session_state.pop(key, None)
        st.session_state["supabase_user_role"] = current_role

if "default_data" not in st.session_state:
    account_email = st.session_state.get("supabase_user_email", "")
    if user_role(account_email) == "admin":
        st.session_state["default_data"] = read_default_data()
    else:
        st.session_state["default_data"] = read_user_template(account_email)
if "draft_data" not in st.session_state:
    draft, saved_signature, load_error = load_custom_draft(st.session_state["default_data"])
    st.session_state["draft_data"] = draft
    st.session_state["saved_draft_signature"] = saved_signature
    st.session_state["draft_load_error"] = load_error
    st.session_state["draft_revision"] = 0
    st.session_state["active_saved_resume_id"] = None
    st.session_state["active_saved_resume_name"] = ""
st.session_state.setdefault("active_saved_resume_id", None)
st.session_state.setdefault("active_saved_resume_name", "")

st.title("Resume Workshop")
st.markdown("Generate, customize, and manage your resume files.")

with st.sidebar:
    if PERSISTENCE_MODE == "supabase":
        st.caption(st.session_state.get("supabase_user_email", ""))
        if st.button("Sign out", icon=":material/logout:", key="supabase-sign-out"):
            try:
                get_supabase_client().auth.sign_out()
            except Exception:
                pass
            for key in list(st.session_state):
                if key.startswith("draft-") or key in {
                    "supabase_client",
                    "supabase_user_id",
                    "supabase_user_email",
                    "supabase_user_role",
                    "default_data",
                    "draft_data",
                    "saved_draft_signature",
                    "draft_load_error",
                    "draft_revision",
                    "active_saved_resume_id",
                    "active_saved_resume_name",
                    "generated_artifact",
                    "history_pdf_artifact",
                    "generation_issues",
                }:
                    st.session_state.pop(key, None)
            st.rerun()
        st.divider()

    variants_by_label = {
        variant["label"]: variant_id
        for variant_id, variant in st.session_state["default_data"]["variants"].items()
    }
    selected_label = st.selectbox("Resume version", options=list(variants_by_label), key="resume-variant")
    variant_id = variants_by_label[selected_label]
    layout_label = st.selectbox("PDF design", options=list(PDF_LAYOUTS), key="pdf-layout")
    layout_id = PDF_LAYOUTS[layout_label]
    workspace = st.radio(
        "Workspace",
        ["Generate", "Customize", "Saved drafts", "PDF downloads"],
        key="workspace-mode",
    )

variant = st.session_state["draft_data"]["variants"][variant_id]

if workspace == "Generate":
    default_variant = st.session_state["default_data"]["variants"][variant_id]
    st.subheader(default_variant["label"])
    st.markdown(f"**{default_variant['headline']}**")
    if variant_id == "customer_relations":
        st.write(default_variant["objective"])
        metrics = st.columns(3)
        metrics[0].metric("Skills", len(default_variant["skills"]))
        metrics[1].metric("Experience entries", len(default_variant["experience"]))
        metrics[2].metric("Achievements", len(default_variant["achievements"]))
    else:
        st.write(default_variant["summary"])
        metrics = st.columns(3)
        metrics[0].metric("Skill groups", len(default_variant["skills"]))
        metrics[1].metric("Experience entries", len(default_variant["experience"]))
        metrics[2].metric("Projects", len(default_variant["projects"]))

    payload = st.session_state["default_data"]
    render_generate_button(
        variant_id,
        payload,
        data_signature(payload),
        "Generate default PDF",
        layout_id=layout_id,
    )
elif workspace == "Customize":
    draft = st.session_state["draft_data"]
    draft_name = st.session_state.get("active_saved_resume_name", "")
    if PERSISTENCE_MODE == "supabase":
        if not draft_name:
            draft_name = f"Untitled {variant['label']} resume"
        draft_name = st.text_input(
            "Draft name",
            value=draft_name,
            key=editor_key("draft-name"),
        )
    tabs = st.tabs(["Profile", "Skills", "Experience", "Projects", "Preview"])

    with tabs[0]:
        profile = draft["profile"]
        st.subheader("Contact details")
        first, second = st.columns(2)
        with first:
            edit_text(profile, "name", "Name", "profile-name")
            edit_text(profile, "location", "Location", "profile-location")
        with second:
            edit_text(profile, "email", "Email", "profile-email")
            edit_text(profile, "phone", "Phone", "profile-phone")

        if variant_id == "customer_relations":
            st.subheader("Profile photo")
            uploaded_photo = st.file_uploader(
                "Upload a JPG, JPEG, PNG, or WebP photo",
                type=["jpg", "jpeg", "png", "webp"],
                key=editor_key("customer-photo-upload"),
            )
            if uploaded_photo:
                encoded = base64.b64encode(uploaded_photo.getvalue()).decode("ascii")
                profile["photo_base64"] = f"data:{uploaded_photo.type};base64,{encoded}"
                st.image(uploaded_photo, width=180)
            elif profile.get("photo_base64"):
                st.image(profile["photo_base64"], width=180)
            elif profile.get("photo_path"):
                photo_path = Path(profile["photo_path"])
                if not photo_path.is_absolute():
                    photo_path = PROJECT_DIR / photo_path
                if photo_path.exists():
                    st.image(str(photo_path), width=180)

        st.subheader("Links")
        render_collection(
            profile["links"],
            "Links",
            "profile-links",
            lambda: {"label": "", "url": ""},
            draw_link,
            lambda item: item.get("label", "") or "New link",
        )
        st.subheader("Education")
        render_collection(
            draft["education"],
            "Education entries",
            "education",
            lambda: (
                {"school": "", "degree": "", "year": "", "score": ""}
                if variant_id == "customer_relations"
                else {"degree": "", "year": ""}
            ),
            draw_education,
            lambda item: (
                item.get("school", "") or item.get("degree", "") or "New education entry"
            ),
        )
        st.subheader("Resume heading")
        edit_text(variant, "headline", "Headline", f"{variant_id}-headline")
        if variant_id == "customer_relations":
            edit_text(variant, "objective", "Objective", f"{variant_id}-objective", multiline=True, height=130)
            edit_lines(variant, "achievements", "Achievements", f"{variant_id}-achievements", height=130)
        else:
            edit_text(variant, "summary", "Summary", f"{variant_id}-summary", multiline=True, height=130)
        edit_text(variant, "output_name", "PDF filename prefix", f"{variant_id}-output-name")

    with tabs[1]:
        if variant_id == "customer_relations":
            st.subheader("Skills")
            edit_lines(variant, "skills", "Skills", f"{variant_id}-skills", height=130)
        else:
            st.subheader("Skill groups")
            render_collection(
            variant["skills"],
            "Skill groups",
            f"{variant_id}-skills",
            lambda: {"label": "", "items": []},
            draw_skill,
            lambda item: item.get("label", "") or "New skill group",
        )

    with tabs[2]:
        st.subheader("Experience")
        render_collection(
            variant["experience"],
            "Experience entries",
            f"{variant_id}-experience",
            lambda: {"title": "", "company": "", "dates": "", "bullets": []},
            draw_experience,
            lambda item: item.get("title", "") or "New role",
        )

    with tabs[3]:
        if variant_id == "customer_relations":
            st.subheader("Projects")
            st.info("The Customer Relations layout does not include a projects section.")
        else:
            st.subheader("Projects")
            render_collection(
            variant["projects"],
            "Projects",
            f"{variant_id}-projects",
            lambda: {
                "title": "",
                "organization": "",
                "role": "",
                "team": "",
                "technologies": [],
                "context": "",
                "description": "",
                "bullets": [],
            },
            draw_project,
            lambda item: item.get("title", "") or "New project",
        )

    with tabs[4]:
        st.subheader(variant["headline"] or "Resume preview")
        if variant_id == "customer_relations":
            st.write(variant["objective"])
            st.markdown("**Skills**")
            st.write(" · ".join(variant["skills"]))
            st.markdown("**Experience**")
            st.write(" · ".join(job["title"] for job in variant["experience"] if job.get("title")))
            st.markdown("**Achievements**")
            st.write(" · ".join(variant["achievements"]))
        else:
            st.write(variant["summary"])
            st.markdown("**Skills**")
            st.write(" · ".join(skill["label"] for skill in variant["skills"] if skill.get("label")))
            st.markdown("**Experience**")
            st.write(" · ".join(job["title"] for job in variant["experience"] if job.get("title")))
            st.markdown("**Projects**")
            st.write(" · ".join(project["title"] for project in variant["projects"] if project.get("title")))

    signature = (
        saved_resume_signature(draft, draft_name, variant_id)
        if PERSISTENCE_MODE == "supabase"
        else data_signature(draft)
    )
    saved_signature = st.session_state.get("saved_draft_signature")
    if st.session_state.get("draft_load_error"):
        st.error(st.session_state["draft_load_error"])
    if saved_signature is None:
        st.info("This is an unsaved draft. Save it to the library when ready.")
    elif signature == saved_signature:
        st.success("Draft saved. No unsaved changes.")
    else:
        st.warning("You have unsaved changes.")

    if (
        PERSISTENCE_MODE == "supabase"
        and st.session_state.get("supabase_user_role") == "admin"
        and saved_signature is None
        and CUSTOM_DATA_PATH.exists()
    ):
        st.info("A local custom draft is available to import. Importing keeps the local copy.")
        import_confirmed = st.checkbox(
            "Confirm import of the local draft to Supabase",
            key=editor_key("confirm-local-import"),
        )
        if st.button(
            "Import local draft",
            icon=":material/cloud_upload:",
            key="import-local-draft",
            disabled=not import_confirmed or bool(st.session_state.get("draft_load_error")),
        ):
            try:
                local_draft = read_local_custom_draft(st.session_state["default_data"])
                imported_record = save_resume(
                    get_supabase_client(),
                    st.session_state["supabase_user_id"],
                    "Imported local draft",
                    variant_id,
                    clean_editor_ids(local_draft),
                )
                st.session_state["draft_data"] = local_draft
                st.session_state["active_saved_resume_id"] = imported_record["id"]
                st.session_state["active_saved_resume_name"] = imported_record["name"]
                st.session_state["saved_draft_signature"] = saved_resume_signature(
                    local_draft,
                    imported_record["name"],
                    variant_id,
                )
                st.session_state["draft_load_error"] = None
                st.session_state["draft_revision"] += 1
                st.session_state.pop("generated_artifact", None)
                st.session_state.pop("generation_issues", None)
                st.rerun()
            except Exception as error:
                st.error(f"Could not import the local draft: {error}")

    if PERSISTENCE_MODE == "supabase":
        update_column, new_column, reset_column = st.columns(3)
        with update_column:
            if st.button(
                "Update saved draft",
                icon=":material/save:",
                key="update-saved-resume",
                disabled=(
                    not st.session_state.get("active_saved_resume_id")
                    or not draft_name.strip()
                    or bool(st.session_state.get("draft_load_error"))
                ),
            ):
                try:
                    record = save_resume(
                        get_supabase_client(),
                        st.session_state["supabase_user_id"],
                        draft_name,
                        variant_id,
                        clean_editor_ids(draft),
                        resume_id=st.session_state["active_saved_resume_id"],
                    )
                    st.session_state["active_saved_resume_name"] = record["name"]
                    st.session_state["saved_draft_signature"] = saved_resume_signature(
                        draft, record["name"], variant_id
                    )
                    st.session_state.pop("draft_load_error", None)
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not update the saved draft: {error}")
        with new_column:
            if st.button(
                "Save as new draft",
                icon=":material/note_add:",
                key="save-as-new-resume",
                disabled=not draft_name.strip() or bool(st.session_state.get("draft_load_error")),
            ):
                try:
                    record = save_resume(
                        get_supabase_client(),
                        st.session_state["supabase_user_id"],
                        draft_name,
                        variant_id,
                        clean_editor_ids(draft),
                    )
                    st.session_state["active_saved_resume_id"] = record["id"]
                    st.session_state["active_saved_resume_name"] = record["name"]
                    st.session_state["saved_draft_signature"] = saved_resume_signature(
                        draft, record["name"], variant_id
                    )
                    st.session_state.pop("draft_load_error", None)
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not save the new draft: {error}")
        with reset_column:
            reset_confirmed = st.checkbox(
                "Confirm discard",
                key=editor_key("confirm-reset"),
            )
            if st.button(
                "Reset editor",
                icon=":material/restore:",
                key="reset-resume-editor",
                disabled=not reset_confirmed,
            ):
                st.session_state["draft_data"] = attach_editor_ids(
                    copy.deepcopy(st.session_state["default_data"])
                )
                st.session_state["saved_draft_signature"] = None
                st.session_state["active_saved_resume_id"] = None
                st.session_state["active_saved_resume_name"] = ""
                st.session_state["draft_load_error"] = None
                st.session_state["draft_revision"] += 1
                st.session_state.pop("generated_artifact", None)
                st.session_state.pop("generation_issues", None)
                st.rerun()
    else:
        save_column, reset_column = st.columns([1, 2])
        with save_column:
            if st.button("Save draft", icon=":material/save:", key="save-custom-draft"):
                try:
                    save_custom_draft(draft, st.session_state["default_data"])
                    st.session_state["saved_draft_signature"] = signature
                    st.session_state["draft_load_error"] = None
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not save the draft: {error}")
        with reset_column:
            reset_confirmed = st.checkbox(
                "Confirm reset to default data",
                key=editor_key("confirm-reset"),
            )
            if st.button(
                "Reset custom draft",
                icon=":material/restore:",
                key="reset-custom-draft",
                disabled=not reset_confirmed,
            ):
                try:
                    CUSTOM_DATA_PATH.unlink(missing_ok=True)
                    st.session_state["draft_data"] = attach_editor_ids(
                        copy.deepcopy(st.session_state["default_data"])
                    )
                    st.session_state["saved_draft_signature"] = None
                    st.session_state["draft_load_error"] = None
                    st.session_state["draft_revision"] += 1
                    st.session_state.pop("generated_artifact", None)
                    st.session_state.pop("generation_issues", None)
                    st.rerun()
                except OSError as error:
                    st.error(f"Could not reset the draft: {error}")

    validation_issues = validate_resume(draft, variant_id)
    if validation_issues:
        st.warning(f"{len(validation_issues)} field checks need attention before PDF generation.")
        with st.expander("Review validation details"):
            for issue in validation_issues:
                st.write(f"- {issue}")
    render_generate_button(
        variant_id,
        draft,
        signature,
        "Generate customized PDF",
        layout_id=layout_id,
        resume_name=draft_name if PERSISTENCE_MODE == "supabase" else None,
        saved_resume_id=st.session_state.get("active_saved_resume_id"),
    )
elif workspace == "Saved drafts":
    st.subheader("Saved drafts")
    if PERSISTENCE_MODE != "supabase":
        st.info("Saved draft library is available when signed in to Supabase.")
    else:
        if st.session_state.get("library_error"):
            st.error(st.session_state.pop("library_error"))
        try:
            saved_resumes = list_saved_resumes(
                get_supabase_client(),
                st.session_state["supabase_user_id"],
            )
        except Exception as error:
            saved_resumes = []
            st.error(f"Could not load saved drafts: {error}")

        if not saved_resumes:
            st.info("No saved drafts yet. Customize a resume and save it to see it here.")

        for saved_resume in saved_resumes:
            variant_label = st.session_state["default_data"]["variants"].get(
                saved_resume["variant_id"], {}
            ).get("label", saved_resume["variant_id"])
            with st.expander(f"{saved_resume['name']}  ·  {variant_label}"):
                st.caption(f"Updated {saved_resume['updated_at']}")
                open_column, pdf_column, delete_column = st.columns(3)
                open_column.button(
                    "Open in editor",
                    icon=":material/edit:",
                    key=f"open-saved-{saved_resume['id']}",
                    on_click=open_saved_resume,
                    args=(saved_resume["id"],),
                )
                if pdf_column.button(
                    "Generate PDF",
                    icon=":material/picture_as_pdf:",
                    key=f"prepare-saved-pdf-{saved_resume['id']}",
                ):
                    try:
                        full_record = get_saved_resume(
                            get_supabase_client(),
                            st.session_state["supabase_user_id"],
                            saved_resume["id"],
                        )
                        prepare_saved_resume_pdf(full_record, layout_id)
                    except Exception as error:
                        st.error(f"Could not prepare this resume: {error}")

                confirm_delete = delete_column.checkbox(
                    "Confirm delete",
                    key=f"confirm-delete-saved-{saved_resume['id']}",
                )
                if delete_column.button(
                    "Delete draft",
                    icon=":material/delete:",
                    key=f"delete-saved-{saved_resume['id']}",
                    disabled=not confirm_delete,
                ):
                    try:
                        delete_resume(
                            get_supabase_client(),
                            st.session_state["supabase_user_id"],
                            saved_resume["id"],
                        )
                        if st.session_state.get("active_saved_resume_id") == saved_resume["id"]:
                            st.session_state["active_saved_resume_id"] = None
                            st.session_state["active_saved_resume_name"] = ""
                            st.session_state["saved_draft_signature"] = None
                        st.session_state.pop("generated_artifact", None)
                        st.rerun()
                    except Exception as error:
                        st.error(f"Could not delete this draft: {error}")

                artifact = st.session_state.get("generated_artifact")
                if artifact and artifact.get("saved_resume_id") == saved_resume["id"]:
                    render_download(artifact["variant_id"], artifact["signature"], layout_id)
elif workspace == "PDF downloads":
    st.subheader("PDF downloads")
    if PERSISTENCE_MODE != "supabase":
        st.info("PDF history is available when signed in to Supabase.")
    else:
        try:
            pdf_history = list_pdf_history(
                get_supabase_client(),
                st.session_state["supabase_user_id"],
            )
        except Exception as error:
            pdf_history = []
            st.error(f"Could not load PDF history: {error}")

        if not pdf_history:
            st.info("No PDF downloads yet. Download a generated resume to add it here.")

        for pdf_record in pdf_history:
            variant_label = st.session_state["default_data"]["variants"].get(
                pdf_record["variant_id"], {}
            ).get("label", pdf_record["variant_id"])
            with st.container(border=True):
                details, action = st.columns([4, 1])
                details.markdown(f"**{pdf_record['filename']}**")
                details.caption(
                    f"{pdf_record['resume_name']}  ·  {variant_label}  ·  "
                    f"Download requested {pdf_record['download_requested_at']}"
                )
                if action.button(
                    "Retrieve",
                    icon=":material/download:",
                    key=f"retrieve-pdf-{pdf_record['id']}",
                ):
                    try:
                        filename, content = get_pdf_download(
                            get_supabase_client(),
                            st.session_state["supabase_user_id"],
                            pdf_record["id"],
                        )
                        st.session_state["history_pdf_artifact"] = {
                            "id": pdf_record["id"],
                            "filename": filename,
                            "content": content,
                        }
                    except Exception as error:
                        st.error(f"Could not retrieve this PDF: {error}")

                artifact = st.session_state.get("history_pdf_artifact")
                if artifact and artifact["id"] == pdf_record["id"]:
                    st.download_button(
                        "Download PDF",
                        data=artifact["content"],
                        file_name=artifact["filename"],
                        mime="application/pdf",
                        icon=":material/download:",
                        key=f"download-history-pdf-{pdf_record['id']}",
                    )
