from datetime import datetime, timezone
from uuid import uuid4


SAVED_RESUMES_TABLE = "saved_resumes"
PDF_HISTORY_TABLE = "resume_pdf_downloads"
PDF_BUCKET = "resume-pdfs"


def list_saved_resumes(client, user_id):
    result = (
        client.table(SAVED_RESUMES_TABLE)
        .select("id,name,variant_id,created_at,updated_at")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .execute()
    )
    return result.data or []


def get_saved_resume(client, user_id, resume_id):
    result = (
        client.table(SAVED_RESUMES_TABLE)
        .select("id,name,variant_id,data,created_at,updated_at")
        .eq("id", resume_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise ValueError("The saved resume was not found in this account.")
    return result.data[0]


def save_resume(client, user_id, name, variant_id, data, resume_id=None):
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "user_id": user_id,
        "name": name.strip(),
        "variant_id": variant_id,
        "data": data,
        "updated_at": now,
    }
    if resume_id:
        result = (
            client.table(SAVED_RESUMES_TABLE)
            .update(record)
            .eq("id", resume_id)
            .eq("user_id", user_id)
            .execute()
        )
    else:
        record["created_at"] = now
        result = client.table(SAVED_RESUMES_TABLE).insert(record).execute()

    if not result.data:
        raise RuntimeError("The saved resume could not be confirmed in Supabase.")
    return result.data[0]


def delete_resume(client, user_id, resume_id):
    result = (
        client.table(SAVED_RESUMES_TABLE)
        .delete()
        .eq("id", resume_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise RuntimeError("The saved resume was not found or could not be deleted.")


def list_pdf_history(client, user_id):
    result = (
        client.table(PDF_HISTORY_TABLE)
        .select("id,saved_resume_id,resume_name,variant_id,filename,download_requested_at")
        .eq("user_id", user_id)
        .order("download_requested_at", desc=True)
        .execute()
    )
    return result.data or []


def record_pdf_download(
    client,
    user_id,
    pdf_bytes,
    filename,
    resume_name,
    variant_id,
    saved_resume_id=None,
):
    pdf_id = str(uuid4())
    storage_path = f"{user_id}/{pdf_id}.pdf"
    storage = client.storage.from_(PDF_BUCKET)
    storage.upload(
        storage_path,
        pdf_bytes,
        file_options={"content-type": "application/pdf", "upsert": "false"},
    )

    record = {
        "id": pdf_id,
        "user_id": user_id,
        "saved_resume_id": saved_resume_id,
        "resume_name": resume_name,
        "variant_id": variant_id,
        "filename": filename,
        "storage_path": storage_path,
        "download_requested_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        result = client.table(PDF_HISTORY_TABLE).insert(record).execute()
        if not result.data:
            raise RuntimeError("The PDF history record was not confirmed in Supabase.")
        return result.data[0]
    except Exception:
        storage.remove([storage_path])
        raise


def get_pdf_download(client, user_id, pdf_id):
    result = (
        client.table(PDF_HISTORY_TABLE)
        .select("id,filename,storage_path")
        .eq("id", pdf_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise ValueError("The PDF is not available in this account's history.")

    record = result.data[0]
    content = client.storage.from_(PDF_BUCKET).download(record["storage_path"])
    return record["filename"], content
