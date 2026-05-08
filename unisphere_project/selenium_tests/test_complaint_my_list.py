import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "unisphere.settings")

import django
django.setup()

from django.contrib.auth import get_user_model
from complaints.models import Complaint

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


# Setup: create a student with some complaints
student = ensure_user("selenium_complaint_lister", role="student")

UNIQUE_SUBJECT = "SeleniumComplaintList_QRS555"
Complaint.objects.filter(subject=UNIQUE_SUBJECT).delete()

# Create two complaints — one submitted, one resolved
complaint_1 = Complaint.objects.create(
    subject=UNIQUE_SUBJECT,
    description="First complaint for list test — submitted status.",
    category="academic",
    status="submitted",
    submitted_by=student,
    target_type="admin",
)

complaint_2 = Complaint.objects.create(
    subject=f"{UNIQUE_SUBJECT}_Resolved",
    description="Second complaint for list test — resolved status.",
    category="infrastructure",
    status="resolved",
    submitted_by=student,
    target_type="admin",
)

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    # Step 1: Login as the student who submitted complaints
    login(driver, "selenium_complaint_lister", PASSWORD)

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Step 2: Navigate to My Complaints page
    driver.get(f"{BASE_URL}/complaints/my/")

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    assert "/complaints/my" in driver.current_url, (
        f"My complaints page did not load.\nURL: {driver.current_url}"
    )

    print("My Complaints Page Loaded ✅")

    # Step 3: Verify submitted complaint appears
    page_source = driver.page_source

    assert UNIQUE_SUBJECT in page_source, (
        f"Submitted complaint '{UNIQUE_SUBJECT}' not found on my complaints page."
    )

    print("Submitted Complaint Visible ✅")

    # Step 4: Verify resolved complaint also appears
    assert f"{UNIQUE_SUBJECT}_Resolved" in page_source, (
        "Resolved complaint not found on my complaints page."
    )

    print("Resolved Complaint Visible ✅")

    # Step 5: Click on first complaint to view detail
    complaint_links = driver.execute_script("""
        return Array.from(document.querySelectorAll('a'))
            .map(a => a.href)
            .filter(href => href.includes('/complaints/'))
            .filter(href => {
                let parts = href.replace(/\\/$/, '').split('/');
                return /^\\d+$/.test(parts[parts.length - 1]);
            });
    """)

    if complaint_links:
        driver.get(complaint_links[0])

        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        assert "/complaints/" in driver.current_url, (
            f"Complaint detail page did not load.\nURL: {driver.current_url}"
        )

        print("Complaint Detail Page Loaded ✅")
    else:
        print("No complaint detail links found — Skipped detail step")

    print("My Complaints List Test Passed ✅")

finally:
    # Cleanup
    Complaint.objects.filter(subject__startswith=UNIQUE_SUBJECT).delete()
    driver.quit()
