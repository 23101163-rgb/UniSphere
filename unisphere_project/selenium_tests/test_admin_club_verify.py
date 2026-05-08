import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "unisphere.settings")

import django
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import ClubMembership

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


# Setup: create a student with an unverified club membership
student = ensure_user("selenium_club_pending", role="student")
student.is_club_member = True
student.save()

# Ensure a pending (unverified) club membership exists
membership, created = ClubMembership.objects.get_or_create(
    user=student,
    club_name="math_club",
    defaults={
        "club_position": "member",
        "is_verified": False,
        "authorized_to_post": False,
    },
)

if not created:
    # Reset to unverified state for the test
    membership.is_verified = False
    membership.authorized_to_post = False
    membership.save()

membership_pk = membership.pk

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    # Step 1: Login as admin
    login(driver, ADMIN_USERNAME, ADMIN_PASSWORD)

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Step 2: Navigate to club verification page
    driver.get(f"{BASE_URL}/accounts/club-verification/")

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    assert "/accounts/club-verification" in driver.current_url, (
        f"Club verification page did not load.\nURL: {driver.current_url}"
    )

    print("Club Verification Page Loaded ✅")

    # Step 3: Verify the pending membership appears
    page_source = driver.page_source

    assert "selenium_club_pending" in page_source or "Math Club" in page_source, (
        "Pending club membership not found on verification page."
    )

    print("Pending Membership Visible ✅")

    # Step 4: Verify the club membership by hitting the verify URL
    driver.get(f"{BASE_URL}/accounts/club-verify/{membership_pk}/")

    wait.until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

    # Step 5: Verify in DB that membership is now verified
    membership.refresh_from_db()
    assert membership.is_verified, (
        f"Club membership pk={membership_pk} should be verified but is_verified={membership.is_verified}"
    )

    print("Club Membership Verified in Database ✅")
    print("Admin Club Verification Test Passed ✅")

finally:
    driver.quit()
