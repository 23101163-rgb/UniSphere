import os
import sys
import time
from datetime import date, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "unisphere.settings")

import django
django.setup()

from django.contrib.auth import get_user_model
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from common import get_driver, login, BASE_URL
from jobs.models import JobListing

User = get_user_model()


def ensure_user(username, password, role="student", email=None, **extra):
    email = email or f"{username}@uap-bd.edu"

    user, _ = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "role": role,
            "department": "CSE",
            "university_id": extra.pop(
                "university_id",
                f"U{abs(hash(username)) % 1000000:06d}"
            ),
        },
    )

    user.email = email
    user.role = role
    user.department = extra.pop("department", "CSE")

    if not user.university_id:
        user.university_id = f"U{abs(hash(username)) % 1000000:06d}"

    for key, value in extra.items():
        setattr(user, key, value)

    user.set_password(password)
    user.save()
    return user


def wait_page_ready(driver, timeout=10):
    wait = WebDriverWait(driver, timeout)
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    return wait


def set_if_present(driver, name, value):
    elements = driver.find_elements(By.NAME, name)

    if not elements:
        return False

    field = elements[0]
    tag = field.tag_name.lower()

    if tag == "select":
        select = Select(field)

        try:
            select.select_by_value(value)
        except Exception:
            try:
                select.select_by_visible_text(value)
            except Exception:
                valid_options = [
                    option.get_attribute("value")
                    for option in select.options
                    if option.get_attribute("value")
                ]

                if valid_options:
                    select.select_by_value(valid_options[0])
                else:
                    raise
    else:
        driver.execute_script(
            """
            arguments[0].value = arguments[1];
            arguments[0].setAttribute('value', arguments[1]);
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            """,
            field,
            value
        )

    return True


def set_date_field(driver, name, value):
    elements = driver.find_elements(By.NAME, name)

    if not elements:
        raise AssertionError(f'Date field "{name}" not found.')

    field = elements[0]

    driver.execute_script(
        """
        arguments[0].removeAttribute('readonly');
        arguments[0].value = arguments[1];
        arguments[0].setAttribute('value', arguments[1]);
        arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
        arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """,
        field,
        value
    )

    actual_value = field.get_attribute("value")

    if actual_value != value:
        raise AssertionError(
            f'Date field "{name}" was not set correctly. '
            f'Expected: {value}, Got: {actual_value}'
        )


def wait_for_job(title, timeout=10):
    for _ in range(timeout * 2):
        if JobListing.objects.filter(title=title).exists():
            return True
        time.sleep(0.5)

    return False


def collect_page_errors(driver):
    selectors = [
        ".alert",
        ".text-danger",
        ".text-warning",
        ".invalid-feedback",
        ".errorlist",
        ".help-block",
    ]

    messages = []

    for selector in selectors:
        for element in driver.find_elements(By.CSS_SELECTOR, selector):
            text = element.text.strip()
            if text:
                messages.append(text)

    return "\n".join(messages)


ADMIN_PASSWORD = "amiraiyan123@#"
JOB_TITLE = "Selenium Backend Intern"

admin = ensure_user(
    username="ARaiyan",
    password=ADMIN_PASSWORD,
    role="admin",
    email="raiyan@uap-bd.edu",
    first_name="A",
    last_name="Raiyan",
    university_id="00001",
)

JobListing.objects.filter(title=JOB_TITLE).delete()

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    login(driver, "ARaiyan", ADMIN_PASSWORD)

    driver.get(f"{BASE_URL}/jobs/create/")
    wait_page_ready(driver)

    try:
        wait.until(EC.presence_of_element_located((By.NAME, "title")))
    except Exception:
        raise AssertionError(
            "Job create page did not load. "
            f"Current URL: {driver.current_url}\n"
            f"Preview: {driver.page_source[:1200].lower()}"
        )

    deadline_value = (date.today() + timedelta(days=10)).strftime("%Y-%m-%d")

    set_if_present(driver, "title", JOB_TITLE)
    set_if_present(driver, "company_name", "Selenium Tech Ltd")
    set_if_present(driver, "job_type", "internship")
    set_if_present(driver, "description", "Selenium job description")
    set_if_present(driver, "required_skills", "Python, Django")
    set_if_present(driver, "eligibility", "CSE students")
    set_if_present(driver, "salary_range", "25000")
    set_date_field(driver, "application_deadline", deadline_value)
    set_if_present(driver, "application_link", "https://example.com/apply")

    submit_buttons = driver.find_elements(
        By.CSS_SELECTOR,
        "button[type='submit'], input[type='submit']"
    )

    if submit_buttons:
        driver.execute_script("arguments[0].click();", submit_buttons[0])
    else:
        driver.find_element(By.TAG_NAME, "form").submit()

    wait_page_ready(driver)

    if not wait_for_job(JOB_TITLE):
        errors = collect_page_errors(driver)

        raise AssertionError(
            "Job was not created.\n"
            f"URL: {driver.current_url}\n"
            f"Form/Page errors:\n{errors or 'No visible error found'}\n"
            f"Preview: {driver.page_source[:1500].lower()}"
        )

    print("Job Create Test Passed ✅")

finally:
    driver.quit()
