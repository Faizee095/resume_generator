import json


def run(app):
    app.run()
    assert not app.exception
    return app


def test_preview_bytes_are_reused_by_generate(local_app_test):
    app = local_app_test
    app.button(key="preview-default-pdf").click()
    run(app)
    preview = app.session_state["pdf_preview_artifact"]
    assert preview["content"].startswith(b"%PDF")
    assert preview["pages"]

    app.button(key="generate-Generate default PDF").click()
    run(app)
    generated = app.session_state["generated_artifact"]
    assert generated["content"] == preview["content"]


def test_preview_page_navigation_advances_and_clamps(local_app_test):
    app = local_app_test
    data = app.session_state["default_data"]
    app.session_state["pdf_preview_artifact"] = {
        "variant_id": "frontend",
        "signature": json.dumps(data, ensure_ascii=False, sort_keys=True),
        "layout_id": "classic",
        "filename": "sample.pdf",
        "content": b"%PDF sample",
        "pages": [b"first page", b"second page"],
        "saved_resume_id": None,
        "viewer_key": "default-pdf",
    }

    app.button(key="preview-default-pdf").click()
    run(app)
    app.button(key="pdf-preview-page-default-pdf-next").click()
    run(app)
    assert app.session_state["pdf-preview-page-default-pdf"] == 1

    app.button(key="preview-default-pdf").click()
    run(app)
    assert app.button(key="pdf-preview-page-default-pdf-next").disabled
    app.button(key="pdf-preview-page-default-pdf-previous").click()
    run(app)
    assert app.session_state["pdf-preview-page-default-pdf"] == 0


def test_custom_draft_changes_mark_preview_stale_and_save_to_isolated_path(
    local_app_test, tmp_path
):
    app = local_app_test
    app.button(key="preview-default-pdf").click()
    run(app)

    app.radio[0].set_value("Customize")
    run(app)
    app.text_input(key="draft-0-frontend-headline").set_value("Updated Sample Headline")
    run(app)
    assert any("preview is out of date" in item.value.lower() for item in app.info)

    app.button(key="save-custom-draft").click()
    run(app)
    saved_path = tmp_path / "resume_custom.json"
    saved_data = json.loads(saved_path.read_text(encoding="utf-8"))
    assert saved_data["variants"]["frontend"]["headline"] == "Updated Sample Headline"


def test_customer_relations_variant_with_empty_experience_bullets_previews(local_app_test):
    app = local_app_test
    app.selectbox[0].select("Customer Relations")
    run(app)
    app.button(key="preview-default-pdf").click()
    run(app)

    assert app.session_state["pdf_preview_artifact"]["variant_id"] == "customer_relations"
    assert not any("Fix these fields" in item.value for item in app.error)


def test_invalid_customize_email_is_rejected_before_preview(local_app_test):
    app = local_app_test
    app.radio[0].set_value("Customize")
    run(app)
    app.text_input(key="draft-0-profile-email").set_value("invalid")
    run(app)
    app.button(key="preview-customized-pdf").click()
    run(app)

    assert any("valid email address" in item.value for item in app.error)
    assert "pdf_preview_artifact" not in app.session_state
