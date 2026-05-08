import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "unisphere.settings")

import django
django.setup()

from django.contrib.auth import get_user_model
from forum.models import Category, Thread, Reply

from common import get_driver, login, BASE_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

User = get_user_model()
PASSWORD = "TestPass123@#"


def ensure_user(username, role="student"):
    user, _ = User.objects.get_or_create(
        username=username,
        defaults={
            "email": f"{username}@uap-bd.edu",
            "role": role,
            "department": "CSE",
            "university_id": f"U{abs(hash(username)) % 1000000:06d}",
        },
    )
    user.role = role
    user.set_password(PASSWORD)
    user.save()
    return user


# Setup: create a thread with a reply
author = ensure_user("selenium_detail_author", role="student")
replier = ensure_user("selenium_detail_replier", role="student")
viewer = ensure_user("selenium_detail_viewer", role="student")

category, _ = Category.objects.get_or_create(
    slug="selenium-detail",
    defaults={"name": "Selenium Detail", "description": "Category for detail test"},
)

UNIQUE_TITLE = "SeleniumDetailThread_XYZ789"
Thread.objects.filter(title=UNIQUE_TITLE).delete()

thread = Thread.objects.create(
    title=UNIQUE_TITLE,
    content="This is the main content of the detail test thread.",
    category=category,
    author=author,
)

Reply.objects.create(
    thread=thread,
    author=replier,
    content="This is a test reply on the detail thread.",
)

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    # Step 1: Login
    login(driver, "selenium_detail_viewer", PASSWORD)

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Step 2: Navigate to thread detail page
    driver.get(f"{BASE_URL}/forum/thread/{thread.pk}/")

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    print("Thread Detail Page Loaded ✅")

    # Step 3: Verify thread title and content appear
    page_source = driver.page_source

    assert UNIQUE_TITLE in page_source, (
        f"Thread title not found on detail page.\nURL: {driver.current_url}"
    )

    print("Thread Title Visible ✅")

    assert "main content of the detail test thread" in page_source, (
        "Thread content not found on detail page."
    )

    print("Thread Content Visible ✅")

    # Step 4: Verify reply appears
    assert "test reply on the detail thread" in page_source, (
        "Reply content not found on thread detail page."
    )

    print("Reply Visible on Thread ✅")

    # Step 5: Verify views count incremented
    thread.refresh_from_db()
    assert thread.views_count >= 1, (
        f"Views count should be at least 1, got {thread.views_count}"
    )

    print("Views Count Incremented ✅")
    print("Forum Thread Detail Test Passed ✅")

finally:
    driver.quit()
