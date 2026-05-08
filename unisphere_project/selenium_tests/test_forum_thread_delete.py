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
author = ensure_user("selenium_delete_author", role="student")

category, _ = Category.objects.get_or_create(
    slug="selenium-delete",
    defaults={"name": "Selenium Delete", "description": "Category for delete test"},
)

UNIQUE_TITLE = "SeleniumDeleteThread_ABC456"
Thread.objects.filter(title=UNIQUE_TITLE).delete()

thread = Thread.objects.create(
    title=UNIQUE_TITLE,
    content="This thread will be deleted by its author via Selenium.",
    category=category,
    author=author,
)

thread_pk = thread.pk

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    # Step 1: Login as the thread author
    login(driver, "selenium_delete_author", PASSWORD)

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Step 2: Navigate to delete URL directly
    # URL pattern: /forum/thread/<pk>/delete/
    driver.get(f"{BASE_URL}/forum/thread/{thread_pk}/delete/")

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    print("Thread Delete Page Loaded ✅")

    # Step 3: Confirm deletion — look for a confirm button/form
    try:
        confirm_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        confirm_btn.click()

        wait.until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        print("Delete Confirmation Submitted ✅")

    except Exception:
        # Some implementations delete on GET directly
        print("No confirm button found — deletion may have happened on GET")

    # Step 4: Verify thread no longer exists in DB
    thread_exists = Thread.objects.filter(pk=thread_pk).exists()
    assert not thread_exists, (
        f"Thread pk={thread_pk} should have been deleted but still exists."
    )

    print("Thread Deleted from Database ✅")
    print("Forum Thread Delete Test Passed ✅")

finally:
    # Cleanup just in case
    Thread.objects.filter(pk=thread_pk).delete()
    driver.quit()
