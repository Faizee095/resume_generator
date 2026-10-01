import copy
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


load_dotenv(PROJECT_DIR / ".env")

DATA_PATH = PROJECT_DIR / "resume_data.json"
CUSTOM_DATA_PATH = PROJECT_DIR / "resume_custom.json"
PERSISTENCE_MODE = os.environ.get("PERSISTENCE_MODE", "local").strip().lower()
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()
ALLOWED_EMAILS = {
    email.strip().lower()
    for email in os.environ.get("ALLOWED_EMAILS", "").split(",")
    if email.strip()
}
SCRIPT_BY_VARIANT = {
    "frontend": "resume_frontend.py",
    "fullstack": "resume_fullstack.py",
    "fullstack_frontend_lead": "resume_fullstack_light_backend.py",
}
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


def get_supabase_client():
    if "supabase_client" not in st.session_state:
        st.session_state["supabase_client"] = create_client(SUPABASE_URL, SUPABASE_KEY)
    return st.session_state["supabase_client"]


def show_login():
    st.title("Resume Workshop")
    st.subheader("Sign in")
    with st.form("supabase-login"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary")

    if submitted:
        if email.strip().lower() not in ALLOWED_EMAILS:
            st.error("This email is not authorized to use this resume workspace.")
            return
        try:
            client = get_supabase_client()
            response = client.auth.sign_in_with_password({
                "email": email.strip(),
                "password": password,
            })
            if response.user is None:
                raise ValueError("Supabase did not return an authenticated user.")
            st.session_state["supabase_user_id"] = response.user.id
            st.session_state["supabase_user_email"] = response.user.email or email.strip()
            st.rerun()
        except Exception:
            st.error("Sign-in failed. Check the credentials and Supabase Auth configuration.")


def attach_editor_ids(data):
    collections = [data["profile"]["links"], data["education"]]
    for variant in data["variants"].values():
        collections.extend((variant["skills"], variant["experience"], variant["projects"]))
    for collection in collections:
        for item in collection:
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
    if not variant.get("summary", "").strip():
        issues.append("Add a summary.")
    if not re.fullmatch(r"[A-Za-z0-9 _-]+", variant.get("output_name", "")):
        issues.append("Use only letters, numbers, spaces, underscores, or hyphens in the PDF filename prefix.")
    if not data.get("education"):
        issues.append("Add at least one education entry.")
    if not variant.get("skills"):
        issues.append("Add at least one skill group.")
    if not variant.get("experience"):
        issues.append("Add at least one experience entry.")
    if not variant.get("projects"):
        issues.append("Add at least one project.")

    for index, link in enumerate(profile.get("links", []), start=1):
        if bool(link.get("label")) != bool(link.get("url")):
            issues.append(f"Contact link {index}: provide both a label and URL, or clear both fields.")
        elif link.get("url") and not link["url"].startswith(("https://", "http://")):
            issues.append(f"Contact link {index}: URL must start with http:// or https://.")

    for index, job in enumerate(variant.get("experience", []), start=1):
        if not job.get("title", "").strip() or not job.get("company", "").strip():
            issues.append(f"Experience {index}: add both a job title and company.")
        if not any(line.strip() for line in job.get("bullets", [])):
            issues.append(f"Experience {index}: add at least one bullet.")

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
        for field in ("skills", "experience", "projects"):
            if not isinstance(variant.get(field), list):
                raise ValueError(f"The saved {variant_id} draft has invalid {field} data.")


def load_custom_draft(defaults):
    if PERSISTENCE_MODE == "supabase":
        try:
            result = (
                get_supabase_client()
                .table("resume_drafts")
                .select("data")
                .eq("user_id", st.session_state["supabase_user_id"])
                .limit(1)
                .execute()
            )
            if not result.data:
                return attach_editor_ids(copy.deepcopy(defaults)), None, None
            saved_data = result.data[0]["data"]
            validate_draft_structure(saved_data, defaults)
            return attach_editor_ids(saved_data), data_signature(saved_data), None
        except Exception:
            message = "Could not load the saved Supabase draft. Saving is paused to protect existing cloud data."
            return attach_editor_ids(copy.deepcopy(defaults)), None, message

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


def generate_pdf(variant_id, resume_data):
    clean_data = clean_editor_ids(resume_data)
    with tempfile.TemporaryDirectory(prefix="resume-workshop-") as temporary_directory:
        temporary_path = Path(temporary_directory)
        custom_data_path = temporary_path / "resume_data.json"
        custom_data_path.write_text(json.dumps(clean_data, ensure_ascii=False), encoding="utf-8")

        environment = os.environ.copy()
        environment["RESUME_DATA_PATH"] = str(custom_data_path)
        environment["RESUME_OUTPUT_DIR"] = str(temporary_path)
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
        return pdf_path.name, pdf_path.read_bytes()


def render_download(variant_id, signature):
    artifact = st.session_state.get("generated_artifact")
    if not artifact:
        return
    if artifact["variant_id"] != variant_id or artifact["signature"] != signature:
        return
    st.download_button(
        "Download PDF",
        data=artifact["content"],
        file_name=artifact["filename"],
        mime="application/pdf",
        icon=":material/download:",
        key="download-current-resume",
    )


def render_generate_button(variant_id, payload, signature, label):
    if st.button(label, type="primary", icon=":material/picture_as_pdf:", key=f"generate-{label}"):
        issues = validate_resume(payload, variant_id)
        if issues:
            st.session_state["generation_issues"] = issues
            st.session_state.pop("generated_artifact", None)
        else:
            st.session_state.pop("generation_issues", None)
            try:
                with st.spinner("Building PDF..."):
                    filename, content = generate_pdf(variant_id, payload)
                st.session_state["generated_artifact"] = {
                    "variant_id": variant_id,
                    "signature": signature,
                    "filename": filename,
                    "content": content,
                }
            except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
                st.session_state.pop("generated_artifact", None)
                st.error(f"Could not generate the PDF: {error}")

    for issue in st.session_state.get("generation_issues", []):
        st.error(issue)
    render_download(variant_id, signature)


def new_record(**fields):
    fields["_editor_id"] = uuid.uuid4().hex
    return fields


if PERSISTENCE_MODE not in {"local", "supabase"}:
    st.error("PERSISTENCE_MODE must be either 'local' or 'supabase'.")
    st.stop()

if PERSISTENCE_MODE == "supabase":
    missing_settings = [
        name for name, value in (
            ("SUPABASE_URL", SUPABASE_URL),
            ("SUPABASE_KEY", SUPABASE_KEY),
            ("ALLOWED_EMAILS", ALLOWED_EMAILS),
        ) if not value
    ]
    if missing_settings:
        st.error(f"Missing required Supabase settings: {', '.join(missing_settings)}")
        st.stop()
    if "supabase_user_id" not in st.session_state or "supabase_client" not in st.session_state:
        show_login()
        st.stop()


if "default_data" not in st.session_state:
    st.session_state["default_data"] = read_default_data()
if "draft_data" not in st.session_state:
    draft, saved_signature, load_error = load_custom_draft(st.session_state["default_data"])
    st.session_state["draft_data"] = draft
    st.session_state["saved_draft_signature"] = saved_signature
    st.session_state["draft_load_error"] = load_error
    st.session_state["draft_revision"] = 0

st.title("Resume Workshop")
st.markdown("Generate from defaults or edit a protected custom draft.")

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
                    "draft_data",
                    "saved_draft_signature",
                    "draft_load_error",
                    "draft_revision",
                    "generated_artifact",
                    "generation_issues",
                }:
                    st.session_state.pop(key, None)
            st.rerun()
        st.divider()

    variants_by_label = {
        variant["label"]: variant_id
        for variant_id, variant in st.session_state["default_data"]["variants"].items()
    }
    selected_label = st.selectbox("Resume version", options=list(variants_by_label))
    variant_id = variants_by_label[selected_label]
    mode = st.radio("Content", ["Default data", "Customize"], horizontal=False)

variant = st.session_state["draft_data"]["variants"][variant_id]

if mode == "Default data":
    default_variant = st.session_state["default_data"]["variants"][variant_id]
    st.subheader(default_variant["label"])
    st.markdown(f"**{default_variant['headline']}**")
    st.write(default_variant["summary"])
    metrics = st.columns(3)
    metrics[0].metric("Skill groups", len(default_variant["skills"]))
    metrics[1].metric("Experience entries", len(default_variant["experience"]))
    metrics[2].metric("Projects", len(default_variant["projects"]))

    payload = st.session_state["default_data"]
    render_generate_button(variant_id, payload, data_signature(payload), "Generate default PDF")
else:
    draft = st.session_state["draft_data"]
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
            lambda: {"degree": "", "year": ""},
            draw_education,
            lambda item: item.get("degree", "") or "New education entry",
        )
        st.subheader("Resume heading")
        edit_text(variant, "headline", "Headline", f"{variant_id}-headline")
        edit_text(variant, "summary", "Summary", f"{variant_id}-summary", multiline=True, height=130)
        edit_text(variant, "output_name", "PDF filename prefix", f"{variant_id}-output-name")

    with tabs[1]:
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
        st.write(variant["summary"])
        st.markdown("**Skills**")
        st.write(" · ".join(skill["label"] for skill in variant["skills"] if skill.get("label")))
        st.markdown("**Experience**")
        st.write(" · ".join(job["title"] for job in variant["experience"] if job.get("title")))
        st.markdown("**Projects**")
        st.write(" · ".join(project["title"] for project in variant["projects"] if project.get("title")))

    signature = data_signature(draft)
    saved_signature = st.session_state.get("saved_draft_signature")
    if st.session_state.get("draft_load_error"):
        st.error(st.session_state["draft_load_error"])
    if saved_signature is None:
        st.info("No saved custom draft yet.")
    elif signature == saved_signature:
        st.success("Draft saved. No unsaved changes.")
    else:
        st.warning("You have unsaved changes.")

    if (
        PERSISTENCE_MODE == "supabase"
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
                save_custom_draft(local_draft, st.session_state["default_data"])
                st.session_state["draft_data"] = local_draft
                st.session_state["saved_draft_signature"] = data_signature(local_draft)
                st.session_state["draft_load_error"] = None
                st.session_state["draft_revision"] += 1
                st.session_state.pop("generated_artifact", None)
                st.session_state.pop("generation_issues", None)
                st.rerun()
            except Exception as error:
                st.error(f"Could not import the local draft: {error}")

    save_column, reset_column = st.columns([1, 2])
    with save_column:
        if st.button(
            "Save draft",
            icon=":material/save:",
            key="save-custom-draft",
            disabled=bool(st.session_state.get("draft_load_error")),
        ):
            try:
                save_custom_draft(draft, st.session_state["default_data"])
                st.session_state["saved_draft_signature"] = signature
                st.session_state["draft_load_error"] = None
                location = "Supabase" if PERSISTENCE_MODE == "supabase" else "this computer"
                st.success(f"Draft saved to {location}.")
            except Exception as error:
                st.error(f"Could not save the draft: {error}")
    with reset_column:
        reset_confirmed = st.checkbox(
            "Confirm reset to the default data",
            key=editor_key("confirm-reset"),
        )
        if st.button("Reset custom draft", icon=":material/restore:", key="reset-custom-draft"):
            if not reset_confirmed:
                st.error("Confirm the reset before continuing.")
            else:
                try:
                    if PERSISTENCE_MODE == "supabase":
                        (
                            get_supabase_client()
                            .table("resume_drafts")
                            .delete()
                            .eq("user_id", st.session_state["supabase_user_id"])
                            .execute()
                        )
                    else:
                        CUSTOM_DATA_PATH.unlink(missing_ok=True)
                    defaults = st.session_state["default_data"]
                    st.session_state["draft_data"] = attach_editor_ids(copy.deepcopy(defaults))
                    st.session_state["saved_draft_signature"] = None
                    st.session_state["draft_load_error"] = None
                    st.session_state["draft_revision"] += 1
                    st.session_state.pop("generated_artifact", None)
                    st.session_state.pop("generation_issues", None)
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not reset the draft: {error}")

    validation_issues = validate_resume(draft, variant_id)
    if validation_issues:
        st.warning(f"{len(validation_issues)} field checks need attention before PDF generation.")
        with st.expander("Review validation details"):
            for issue in validation_issues:
                st.write(f"- {issue}")
    render_generate_button(variant_id, draft, signature, "Generate customized PDF")
