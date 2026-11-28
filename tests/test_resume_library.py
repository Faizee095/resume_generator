from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest

from resume_library import (
    PDF_BUCKET,
    PDF_HISTORY_TABLE,
    SAVED_RESUMES_TABLE,
    delete_resume,
    get_pdf_download,
    get_saved_resume,
    list_saved_resumes,
    record_pdf_download,
    save_resume,
)


def make_client():
    client = MagicMock()
    query = MagicMock()
    for method in ("select", "eq", "order", "limit", "insert", "update", "delete"):
        getattr(query, method).return_value = query
    client.table.return_value = query
    return client, query


def test_list_and_get_saved_resumes_are_scoped_to_the_owner():
    client, query = make_client()
    expected = {"id": "resume-1", "name": "Work", "variant_id": "frontend", "data": {}}
    query.execute.return_value = SimpleNamespace(data=[expected])

    assert list_saved_resumes(client, "user-1") == [expected]
    client.table.assert_called_with(SAVED_RESUMES_TABLE)
    query.eq.assert_called_with("user_id", "user-1")

    query.eq.reset_mock()
    assert get_saved_resume(client, "user-1", "resume-1") == expected
    query.eq.assert_has_calls([call("id", "resume-1"), call("user_id", "user-1")])

    query.execute.return_value = SimpleNamespace(data=[])
    with pytest.raises(ValueError, match="not found in this account"):
        get_saved_resume(client, "user-2", "resume-1")


def test_save_resume_trims_name_and_scopes_updates_to_owner():
    client, query = make_client()
    expected = {"id": "resume-1", "name": "Work"}
    query.execute.return_value = SimpleNamespace(data=[expected])

    result = save_resume(client, "user-1", "  Work  ", "frontend", {"profile": {}})
    inserted = query.insert.call_args.args[0]
    assert result == expected
    assert inserted["name"] == "Work"
    assert inserted["user_id"] == "user-1"
    assert inserted["created_at"] == inserted["updated_at"]

    query.eq.reset_mock()
    save_resume(client, "user-1", "Work", "frontend", {"profile": {}}, resume_id="resume-1")
    assert query.update.call_args.args[0]["user_id"] == "user-1"
    query.eq.assert_has_calls([call("id", "resume-1"), call("user_id", "user-1")])


def test_delete_resume_requires_a_confirmed_owner_scoped_delete():
    client, query = make_client()
    query.execute.return_value = SimpleNamespace(data=[{"id": "resume-1"}])

    delete_resume(client, "user-1", "resume-1")
    query.eq.assert_has_calls([call("id", "resume-1"), call("user_id", "user-1")])

    query.execute.return_value = SimpleNamespace(data=[])
    with pytest.raises(RuntimeError, match="not found or could not be deleted"):
        delete_resume(client, "user-2", "resume-1")


def test_pdf_history_upload_is_rolled_back_when_database_insert_fails():
    client, query = make_client()
    storage = MagicMock()
    bucket = MagicMock()
    storage.from_.return_value = bucket
    client.storage = storage
    client.table.return_value = query
    query.execute.side_effect = RuntimeError("database unavailable")

    with pytest.raises(RuntimeError, match="database unavailable"):
        record_pdf_download(
            client,
            "user-1",
            b"%PDF sample",
            "sample.pdf",
            "Sample",
            "frontend",
        )

    storage.from_.assert_called_once_with(PDF_BUCKET)
    uploaded_path = bucket.upload.call_args.args[0]
    assert uploaded_path.startswith("user-1/")
    bucket.remove.assert_called_once_with([uploaded_path])
    client.table.assert_called_once_with(PDF_HISTORY_TABLE)


def test_pdf_download_checks_owner_before_fetching_storage():
    client, query = make_client()
    storage = MagicMock()
    bucket = MagicMock()
    storage.from_.return_value = bucket
    client.storage = storage
    query.execute.return_value = SimpleNamespace(
        data=[{"filename": "sample.pdf", "storage_path": "user-1/pdf-1.pdf"}]
    )
    bucket.download.return_value = b"%PDF sample"

    assert get_pdf_download(client, "user-1", "pdf-1") == ("sample.pdf", b"%PDF sample")
    query.eq.assert_has_calls([call("id", "pdf-1"), call("user_id", "user-1")])
    storage.from_.assert_called_once_with(PDF_BUCKET)
    bucket.download.assert_called_once_with("user-1/pdf-1.pdf")
