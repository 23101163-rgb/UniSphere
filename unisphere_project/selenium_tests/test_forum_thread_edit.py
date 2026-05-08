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


# Setup: create a thread to edit
author = ensure_user("selenium_edit_author", role="student")

category, _ = Category.objects.get_or_create(
    slug="selenium-edit",
    defaults={"name": "Selenium Edit", "description": "Category for edit test"},
)

ORIGINAL_TITLE = "SeleniumEditThread_OriginalTitle"
UPDATED_TITLE = "SeleniumEditThread_UpdatedTitle999"

Thread.objects.filter(title__in=[ORIGINAL_TITLE, UPDATED_TITLE]).delete()

thread = Thread.objects.create(
    title=ORIGINAL_TITLE,
    content="Original content before editing.",
    category=category,
    author=author,
)

thread_pk = thread.pk

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    # Step 1: Login as the thread author
    login(driver, "selenium_edit_author", PASSWORD)

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Step 2: Navigate to thread edit page
    driver.get(f"{BASE_URL}/forum/thread/{thread_pk}/edit/")

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    print("Thread Edit Page Loaded ✅")

    # Step 3: Update the title
    title_field = wait.until(EC.presence_of_element_located((By.NAME, "title")))
    title_field.clear()
    title_field.send_keys(UPDATED_TITLE)

    # Step 4: Update the content
    content_field = driver.find_element(By.NAME, "content")
    content_field.clear()
    content_field.send_keys("Updated content after Selenium edit test.")

    # Step 5: Submit the form
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    wait.until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

    # Step 6: Verify thread was updated in DB
    thread.refresh_from_db()

    assert thread.title == UPDATED_TITLE, (
        f"Thread title was not updated.\n"
        f"Expected: {UPDATED_TITLE}\n"
        f"Got: {thread.title}"
    )

    print("Thread Title Updated ✅")

    assert "Updated content after Selenium edit test" in thread.content, (
        f"Thread content was not updated.\nGot: {thread.content}"
    )

    print("Thread Content Updated ✅")
    print("Forum Thread Edit Test Passed ✅")

finally:
    # Cleanup
    Thread.objects.filter(pk=thread_pk).delete()
    driver.quit()
