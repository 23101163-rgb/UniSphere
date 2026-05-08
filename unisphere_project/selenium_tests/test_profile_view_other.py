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


# Setup: create the target profile user and the viewer
target_user = ensure_user(
    "selenium_profile_target",
    role="student",
    first_name="TargetFirst",
    last_name="TargetLast",
    bio="This is a test bio for Selenium profile view test.",
)

viewer = ensure_user("selenium_profile_viewer", role="student")

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    # Step 1: Login as the viewer
    login(driver, "selenium_profile_viewer", PASSWORD)

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Step 2: Navigate to the target user's profile
    driver.get(f"{BASE_URL}/accounts/profile/{target_user.pk}/")

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    assert "/accounts/profile/" in driver.current_url, (
        f"Profile page did not load.\nURL: {driver.current_url}"
    )

    print("Other User Profile Page Loaded ✅")

    # Step 3: Verify target user info appears on page
    page_source = driver.page_source

    assert "TargetFirst" in page_source or "TargetLast" in page_source or "selenium_profile_target" in page_source, (
        "Target user's name not found on profile page."
    )

    print("Target User Name Visible ✅")

    # Step 4: Verify bio appears
    assert "test bio for Selenium profile view test" in page_source, (
        "Target user's bio not found on profile page."
    )

    print("Target User Bio Visible ✅")

    # Step 5: Verify we're viewing someone else's profile (not our own)
    # The viewer's name should not be the main profile displayed
    assert "selenium_profile_viewer" not in page_source or "TargetFirst" in page_source, (
        "Page seems to show the viewer's own profile instead of target user."
    )

    print("Correctly Viewing Another User's Profile ✅")
    print("Profile View Other User Test Passed ✅")

finally:
    driver.quit()
