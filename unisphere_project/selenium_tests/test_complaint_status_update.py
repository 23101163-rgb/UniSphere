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
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


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
    user.email = f"{username}@uap-bd.edu"
    user.department = "CSE"
    user.university_id = f"U{abs(hash(username)) % 1000000:06d}"
    user.set_password(PASSWORD)
    user.save()
    return user


def print_debug_info(driver, complaint_id):
    fresh = Complaint.objects.get(pk=complaint_id)

    print("\n========== DEBUG INFO ==========")
    print("Current URL:", driver.current_url)
    print("Page Title:", driver.title)
    print("DB Complaint Status:", fresh.status)
    print("DB Admin Response:", fresh.admin_response)
    print("\nPage Text:")
    print(driver.find_element(By.TAG_NAME, "body").text[:2500])
    print("================================\n")


def wait_for_status(driver, complaint_id, expected_status):
    try:
        WebDriverWait(driver, 10).until(
            lambda d: Complaint.objects.get(pk=complaint_id).status == expected_status
        )
    except TimeoutException:
        print_debug_info(driver, complaint_id)
        fresh = Complaint.objects.get(pk=complaint_id)
        raise AssertionError(
            f"Status should be '{expected_status}', got '{fresh.status}'"
        )


def submit_form(driver):
    form = driver.find_element(By.TAG_NAME, "form")
    driver.execute_script("arguments[0].requestSubmit();", form)


# Setup users
student = ensure_user("selenium_comp_student", role="student")
admin = ensure_user("selenium_comp_admin", role="admin")


# Fresh complaint
Complaint.objects.filter(subject="Selenium Status Update Complaint").delete()

complaint = Complaint.objects.create(
    subject="Selenium Status Update Complaint",
    description="Test complaint for status update.",
    category="academic",
    submitted_by=student,
    target_type="admin",
    status="submitted",
)

assert complaint.status == "submitted", "Setup failed: should start as submitted"


driver = get_driver()

try:
    # Step 1: Login as admin
    login(driver, "selenium_comp_admin", PASSWORD)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Step 2: Open complaint respond page
    driver.get(f"{BASE_URL}/complaints/{complaint.pk}/respond/")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "status"))
    )

    # Step 3: Change status to in_review
    status_dropdown = Select(driver.find_element(By.NAME, "status"))
    status_dropdown.select_by_value("in_review")

    response_field = driver.find_element(By.NAME, "admin_response")
    response_field.clear()
    response_field.send_keys("We are reviewing your complaint, please wait.")

    submit_form(driver)

    # Step 4: Verify first status change
    wait_for_status(driver, complaint.pk, "in_review")

    complaint.refresh_from_db()

    assert complaint.status == "in_review", (
        f"Status should be 'in_review' after first update, got '{complaint.status}'"
    )

    print("First status update passed: submitted → in_review")

    # Step 5: Now move to resolved
    driver.get(f"{BASE_URL}/complaints/{complaint.pk}/respond/")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "status"))
    )

    status_dropdown = Select(driver.find_element(By.NAME, "status"))
    status_dropdown.select_by_value("resolved")

    response_field = driver.find_element(By.NAME, "admin_response")
    response_field.clear()
    response_field.send_keys("Issue has been resolved.")

    submit_form(driver)

    # Step 6: Verify final status
    wait_for_status(driver, complaint.pk, "resolved")

    complaint.refresh_from_db()

    assert complaint.status == "resolved", (
        f"Status should be 'resolved' after second update, got '{complaint.status}'"
    )

    assert "resolved" in complaint.admin_response.lower(), (
        f"Admin response not saved correctly: '{complaint.admin_response}'"
    )

    print("Second status update passed: in_review → resolved")
    print("Complaint Status Update Test Passed ✅")

finally:
    driver.quit()
