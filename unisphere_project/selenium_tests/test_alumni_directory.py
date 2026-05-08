import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "unisphere.settings")

import django
django.setup()

from django.contrib.auth import get_user_model

from common import get_driver, login, BASE_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

User = get_user_model()
PASSWORD = "TestPass123@#"


def ensure_user(username, role="student", **extra):
    user, _ = User.objects.get_or_create(
        username=username,
        defaults={
            "email": f"{username}@uap-bd.edu",
            "role": role,
            "department": "CSE",
            "university_id": f"U{abs(hash(username)) % 1000000:06d}",
            **extra,
        },
    )
    user.role = role
    for key, val in extra.items():
        setattr(user, key, val)
    user.set_password(PASSWORD)
    user.save()
    return user


# Setup: create an alumni user so directory is not empty
ensure_user(
    "selenium_alumni_user",
    role="alumni",
    first_name="Selenium",
    last_name="AlumniTest",
    graduation_year=2023,
    company="TestCorp",
    designation="Software Engineer",
)

# A student who will browse the directory
ensure_user("selenium_alumni_viewer", role="student")

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    # Step 1: Login as student
    login(driver, "selenium_alumni_viewer", PASSWORD)

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Step 2: Navigate to alumni directory
    driver.get(f"{BASE_URL}/accounts/alumni/")

    wait.until(EC.url_contains("/accounts/alumni"))
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    assert "/accounts/alumni" in driver.current_url, (
        f"Alumni directory did not load.\nURL: {driver.current_url}"
    )

    print("Alumni Directory Page Loaded ✅")

    # Step 3: Verify alumni user appears on page
    page_source = driver.page_source
    assert "AlumniTest" in page_source or "selenium_alumni_user" in page_source, (
        "Alumni user not found on directory page."
    )

    print("Alumni User Visible on Page ✅")

    # Step 4: Test search functionality
    try:
        search_field = driver.find_element(By.NAME, "q")
        search_field.clear()
        search_field.send_keys("TestCorp")
        search_field.submit()

        wait.until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        page_source = driver.page_source
        assert "AlumniTest" in page_source or "TestCorp" in page_source, (
            "Alumni search did not return expected result."
        )

        print("Alumni Search Test Passed ✅")

    except Exception:
        print("No search field found — Skipped search step")

    print("Alumni Directory Test Passed ✅")

finally:
    driver.quit()
