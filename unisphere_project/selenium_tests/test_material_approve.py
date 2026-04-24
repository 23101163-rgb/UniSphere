import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "unilink.settings")

import django
django.setup()

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from materials.models import StudyMaterial

from common import get_driver, login, BASE_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException

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


# Setup: student (uploader) + teacher (approver)
student = ensure_user("selenium_mat_student", role="student")
teacher = ensure_user("selenium_mat_approver", role="teacher")

# Always create a fresh pending material for this test
StudyMaterial.objects.filter(title="Selenium Pending Approval Material").delete()

upload_file = SimpleUploadedFile(
    "pending.pdf",
    b"%PDF-1.4 pending approval test",
    content_type="application/pdf"
)

pending_material = StudyMaterial.objects.create(
    title="Selenium Pending Approval Material",
    description="Material waiting for teacher approval",
    course_name="CSE 315",
    semester="3.1",
    topic="Microprocessors",
    tags="exam, 8086",
    file=upload_file,
    uploaded_by=student,
    is_approved=False,
)

assert not pending_material.is_approved, "Setup failed: material should be unapproved"

driver = get_driver()

try:
    # Step 1: Login as teacher
    login(driver, "selenium_mat_approver", PASSWORD)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Step 2: Hit approve URL directly
    driver.get(f"{BASE_URL}/materials/{pending_material.pk}/approve/")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    print("After approve URL:", driver.current_url)

    # Step 3: Verify in DB that material is now approved
    pending_material.refresh_from_db()
    assert pending_material.is_approved, (
        f"Material should be approved after teacher action.\n"
        f"is_approved={pending_material.is_approved}"
    )

    print("Material Approve Test Passed ✅")

finally:
    driver.quit()
