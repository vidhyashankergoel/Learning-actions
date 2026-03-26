import os
import json
import pytest
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Base URL
BASE_URL = os.getenv("APP_BASE_URL", "http://127.0.0.1:5000")


@pytest.fixture(scope="module")
def driver():
    options = webdriver.ChromeOptions()

    # CI-safe Chrome flags
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    options.binary_location = "/usr/bin/google-chrome"

    service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=options)
    yield driver
    driver.quit()


###################################
# UI TESTS (SELENIUM)
###################################

def test_home_endpoint(driver):
    driver.get(f"{BASE_URL}/")
    body_text = driver.find_element(By.TAG_NAME, "body").text
    response = json.loads(body_text)

    assert response["message"] == "Welcome to Task Manager API"


def test_get_tasks(driver):
    driver.get(f"{BASE_URL}/tasks")
    body_text = driver.find_element(By.TAG_NAME, "body").text
    tasks = json.loads(body_text)

    assert isinstance(tasks, list)
    assert len(tasks) >= 2


###################################
# API TEST (CORRECT WAY — NO SELENIUM)
###################################

def test_add_task_via_api():
    # 1. Add task using API
    response = requests.post(
        f"{BASE_URL}/tasks",
        json={"title": "Learn Selenium"}
    )

    assert response.status_code == 200

    # 2. Fetch tasks
    response = requests.get(f"{BASE_URL}/tasks")
    tasks = response.json()

    # 3. Validate
    assert any(task["title"] == "Learn Selenium" for task in tasks)


###################################
# OPTIONAL: VALIDATE UI REFLECTS NEW TASK
###################################

def test_ui_reflects_new_task(driver):
    driver.get(f"{BASE_URL}/tasks")
    body_text = driver.find_element(By.TAG_NAME, "body").text
    tasks = json.loads(body_text)

    assert any(task["title"] == "Learn Selenium" for task in tasks)


###################################
# SCREENSHOT ON FAILURE
###################################

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item):
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call" and rep.failed:
        driver = item.funcargs.get("driver")
        if driver:
            os.makedirs("reports", exist_ok=True)
            driver.save_screenshot("reports/failure.png")