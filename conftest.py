import pytest
import os
import shutil
from datetime import datetime
from playwright.sync_api import sync_playwright

from core.driver import get_driver
from locators.web.variables import BASE_URL
from pages.api.login_api import login_api, get_token
from utils.csv_reader import get_api_data


# ─────────────────────────────────────────
# Trace Base Folder (DO NOT DELETE)
# ─────────────────────────────────────────
TRACE_DIR = "traces"
API_TRACE_DIR = "api_traces"

os.makedirs(TRACE_DIR, exist_ok=True)
os.makedirs(API_TRACE_DIR, exist_ok=True)


# ─────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────
def get_trace_folder(test_file, base_folder=TRACE_DIR):
    file_name = os.path.basename(str(test_file)).replace(".py", "")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    folder = os.path.join(base_folder, file_name, timestamp)
    os.makedirs(folder, exist_ok=True)

    return folder


def zip_folder(folder_path):
    shutil.make_archive(folder_path, 'zip', folder_path)
    print(f"📦 Zipped: {folder_path}.zip")


# ─────────────────────────────────────────
# Mobile Fixture (Appium)
# ─────────────────────────────────────────
@pytest.fixture(scope="function")
def driver(request):
    trace_folder = get_trace_folder(request.node.fspath)

    driver = get_driver()

    yield driver

    # Screenshot after test
    screenshot_path = os.path.join(
        trace_folder,
        f"{request.node.name}.png"
    )
    driver.save_screenshot(screenshot_path)

    driver.quit()

    zip_folder(trace_folder)


# ─────────────────────────────────────────
# API TRACE FIXTURE (🔥 IMPORTANT)
# ─────────────────────────────────────────
# ─────────────────────────────────────────
# API CONTEXT FIXTURE (NO TRACE HERE)
# ─────────────────────────────────────────
@pytest.fixture(scope="function")
def api_context():
    with sync_playwright() as p:
        context = p.request.new_context()
        yield context
        context.dispose()


# ─────────────────────────────────────────
# API AUTH TOKEN (uses Playwright API)
# ─────────────────────────────────────────
@pytest.fixture(scope="session")
def auth_token():
    users = get_api_data("test_data.csv")
    user = users[0]

    with sync_playwright() as p:
        context = p.request.new_context()

        response = login_api(
            context,
            user["username"],
            user["password"]
        )

        token = get_token(response)

        context.dispose()

    assert token is not None, "Login failed in session fixture"
    return token


# ─────────────────────────────────────────
# Web Fixture (Playwright UI Trace)
# ─────────────────────────────────────────
@pytest.fixture(scope="function")
def page(request):
    trace_folder = get_trace_folder(request.node.fspath)

    test_name = request.node.name
    trace_file = os.path.join(trace_folder, f"{test_name}.zip")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )

        # START TRACE
        context.tracing.start(
            screenshots=True,
            snapshots=True,
            sources=True
        )

        page = context.new_page()
        page.goto(BASE_URL, timeout=60000)

        yield page

        # STOP TRACE
        context.tracing.stop(path=trace_file)

        context.close()
        browser.close()

    zip_folder(trace_folder)