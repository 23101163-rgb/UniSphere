import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "unisphere.settings")

import django
django.setup()

from django.contrib.auth import get_user_model
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from common import get_driver, login, BASE_URL
from complaints.models import Complaint
from notifications.models import Notification

User = get_user_model()
PASSWORD = "TestPass123@#"


def ensure_user(username, password, role="student", email=None, **extra):
    email = email or f"{username}@uap-bd.edu"
    user, _ = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "role": role,
            "department": "CSE",
            "university_id": extra.pop("university_id", f"U{abs(hash(username)) % 1000000:06d}"),
        },
    )
    user.email = email
    user.role = role
    user.department = extra.pop("department", "CSE")
    if not user.university_id:
        user.university_id = f"U{abs(hash(username)) % 1000000:06d}"
    for key, value in extra.items():
        setattr(user, key, value)
    user.set_password(password)
    user.save()
    return user


def wait_page_ready(driver, timeout=10):
    wait = WebDriverWait(driver, timeout)
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    return wait


def print_debug_info(driver, complaint_id):
    fresh = Complaint.objects.get(pk=complaint_id)
    print("\n========== COMPLAINT TEACHER RESPONSE DEBUG ==========")
    print("Current URL:", driver.current_url)
    print("DB Complaint Status:", fresh.status)
    print("DB Admin Response:", fresh.admin_response)
    print("Page Text:")
    print(driver.find_element(By.TAG_NAME, "body").text[:2500])
    print("=====================================================\n")


def wait_for_status(driver, complaint_id, expected_status):
    try:
        WebDriverWait(driver, 10).until(
            lambda d: Complaint.objects.get(pk=complaint_id).status == expected_status
        )
    except TimeoutException:
        print_debug_info(driver, complaint_id)
        fresh = Complaint.objects.get(pk=complaint_id)
        raise AssertionError(
            f"Complaint status was not updated. Expected '{expected_status}', got '{fresh.status}'."
        )


def submit_form(driver):
    form = driver.find_element(By.TAG_NAME, "form")
    driver.execute_script("arguments[0].requestSubmit();", form)


teacher = ensure_user(
    username="selenium_complaint_teacher",
    password=PASSWORD,
    role="teacher",
    email="selenium_complaint_teacher@uap-bd.edu",
    first_name="Complaint",
    last_name="Teacher",
)

student = ensure_user(
    username="selenium_complaint_student",
    password=PASSWORD,
    role="student",
    email="selenium_complaint_student@uap-bd.edu",
    first_name="Complaint",
    last_name="Student",
)

Complaint.objects.filter(subject="Selenium Teacher Complaint").delete()

complaint = Complaint.objects.create(
    subject="Selenium Teacher Complaint",
    description="Complaint for teacher response Selenium test.",
    category="academic",
    status="submitted",
    submitted_by=student,
    is_anonymous=False,
    target_type="teacher",
    target_teacher=teacher,
)

Notification.objects.filter(recipient=student, title__icontains="Complaint Update").delete()

driver = get_driver()

try:
    login(driver, "selenium_complaint_teacher", PASSWORD)

    driver.get(f"{BASE_URL}/complaints/{complaint.pk}/respond/")
    wait_page_ready(driver)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "status"))
    )

    Select(driver.find_element(By.NAME, "status")).select_by_value("resolved")

    response = driver.find_element(By.NAME, "admin_response")
    response.clear()
    response.send_keys("Resolved after teacher review by Selenium.")

    submit_form(driver)
    wait_for_status(driver, complaint.pk, "resolved")

    complaint.refresh_from_db()
    assert complaint.status == "resolved", "Complaint status was not updated"
    assert "Resolved after teacher review" in complaint.admin_response, "Complaint response was not saved"

    assert Notification.objects.filter(
        recipient=student,
        title__icontains="Complaint Update",
        message__icontains="Resolved"
    ).exists(), "Complaint update notification was not created"

    print("Complaint Teacher/Admin Response Test Passed ✅")

finally:
    driver.quit()

