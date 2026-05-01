import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "unisphere.settings")

import django
django.setup()

from django.contrib.auth import get_user_model

from forum.models import Category, Thread

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


# Setup
author = ensure_user("selenium_flag_author", role="student")
flagger = ensure_user("selenium_flag_user", role="student")

category, _ = Category.objects.get_or_create(
    slug="selenium-flag",
    defaults={"name": "Selenium Flag", "description": "Category for flag test"},
)

# Always create a fresh unflagged thread
Thread.objects.filter(title="Selenium Flag Test Thread").delete()
thread = Thread.objects.create(
    title="Selenium Flag Test Thread",
    content="This thread will be flagged by selenium.",
    category=category,
    author=author,
    is_flagged=False,
)

assert not thread.is_flagged, "Setup failed: thread should be unflagged"

driver = get_driver()

try:
    # Step 1: Login as flagger (different user from author)
    login(driver, "selenium_flag_user", PASSWORD)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Step 2: Hit flag URL directly
    # URL pattern: /forum/flag/<content_type>/<pk>/
    driver.get(f"{BASE_URL}/forum/flag/thread/{thread.pk}/")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    print("After flag URL:", driver.current_url)

    # Step 3: Verify thread is now flagged in DB
    thread.refresh_from_db()
    assert thread.is_flagged, (
        f"Thread should be flagged after action.\n"
        f"is_flagged={thread.is_flagged}"
    )

    print("Forum Flag Test Passed ✅")

finally:
    driver.quit()

