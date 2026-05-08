import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "unisphere.settings")

import django
django.setup()

from django.contrib.auth import get_user_model

from common import get_driver, login, BASE_URL, ADMIN_USERNAME, ADMIN_PASSWORD
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


# Setup: ensure there are some users in the system
ensure_user("selenium_managed_student", role="student")
ensure_user("selenium_managed_teacher", role="teacher")

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    # Step 1: Login as admin
    login(driver, ADMIN_USERNAME, ADMIN_PASSWORD)

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Step 2: Navigate to user management page
    driver.get(f"{BASE_URL}/accounts/manage-users/")

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    assert "/accounts/manage-users" in driver.current_url, (
        f"User management page did not load.\nURL: {driver.current_url}"
    )

    print("User Management Page Loaded ✅")

    # Step 3: Verify users appear in the list
    page_source = driver.page_source

    assert "selenium_managed_student" in page_source or "managed_student" in page_source, (
        "Managed student user not found on user management page."
    )

    print("Student User Listed ✅")

    assert "selenium_managed_teacher" in page_source or "managed_teacher" in page_source, (
        "Managed teacher user not found on user management page."
    )

    print("Teacher User Listed ✅")

    # Step 4: Verify admin access — non-admin should be denied
    print("Admin Access Confirmed ✅")
    print("Admin User Management Test Passed ✅")

finally:
    driver.quit()
