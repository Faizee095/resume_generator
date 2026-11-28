import copy
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from tests.support import sample_resume_data


PROJECT_DIR = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_DIR / "app.py"


def configure_local_test_environment(monkeypatch, tmp_path):
    data_path = tmp_path / "resume_data.json"
    data_path.write_text(json.dumps(sample_resume_data()), encoding="utf-8")
    monkeypatch.setenv("PERSISTENCE_MODE", "local")
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("RENDER_EXTERNAL_URL", raising=False)
    monkeypatch.setenv("RESUME_DEFAULT_DATA_PATH", str(data_path))
    monkeypatch.setenv("RESUME_CUSTOM_DATA_PATH", str(tmp_path / "resume_custom.json"))
    return data_path


@pytest.fixture
def local_app_test(monkeypatch, tmp_path):
    configure_local_test_environment(monkeypatch, tmp_path)
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(APP_PATH), default_timeout=90)
    app.session_state["default_data"] = copy.deepcopy(sample_resume_data())
    app.run()
    return app


@pytest.fixture(scope="module")
def streamlit_url(tmp_path_factory):
    temp_dir = tmp_path_factory.mktemp("browser-resume-data")
    data_path = temp_dir / "resume_data.json"
    data_path.write_text(json.dumps(sample_resume_data()), encoding="utf-8")

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    environment = os.environ.copy()
    environment["PERSISTENCE_MODE"] = "local"
    environment.pop("RENDER", None)
    environment.pop("RENDER_EXTERNAL_URL", None)
    environment["RESUME_DEFAULT_DATA_PATH"] = str(data_path)
    environment["RESUME_CUSTOM_DATA_PATH"] = str(temp_dir / "resume_custom.json")

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(APP_PATH),
            "--server.address",
            "127.0.0.1",
            "--server.port",
            str(port),
            "--server.headless",
            "true",
        ],
        cwd=PROJECT_DIR,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 60
    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"Streamlit exited before becoming ready (code {process.returncode}).")
            try:
                with urllib.request.urlopen(f"{url}/_stcore/health", timeout=2) as response:
                    if response.status == 200:
                        break
            except (OSError, urllib.error.URLError):
                time.sleep(0.25)
        else:
            raise RuntimeError("Streamlit did not become ready within 60 seconds.")
        yield url
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
