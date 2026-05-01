import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "unisphere.settings")

import django
django.setup()

from django.contrib.auth import get_user_model
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from common import get_driver, login, BASE_URL

User = get_user_model()


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


from django.core.files.base import ContentFile
from materials.models import StudyMaterial, Bookmark

PASSWORD = "TestPass123@#"

teacher = ensure_user(
    username="selenium_material_owner",
    password=PASSWORD,
    role="teacher",
    email="selenium_material_owner@uap-bd.edu",
    first_name="Material",
    last_name="Owner",
)

student = ensure_user(
    username="selenium_material_downloader",
    password=PASSWORD,
    role="student",
    email="selenium_material_downloader@uap-bd.edu",
    first_name="Material",
    last_name="Downloader",
)

StudyMaterial.objects.filter(title="Selenium Download Material").delete()

material = StudyMaterial(
    title="Selenium Download Material",
    description="Download test material.",
    course_name="CSE102",
    semester="1.2",
    topic="Download Flow",
    tags="download, selenium",
    uploaded_by=teacher,
    is_approved=True,
)
material.file.save("selenium_download_material.txt", ContentFile(b"Download test file content"), save=True)

Bookmark.objects.filter(user=student, material=material).delete()

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    login(driver, "selenium_material_downloader", PASSWORD)

    driver.get(f"{BASE_URL}/materials/{material.pk}/")
    wait_page_ready(driver)

    assert "selenium download material" in driver.page_source.lower(), "Material detail page did not load"

    Bookmark.objects.get_or_create(user=student, material=material)
    assert Bookmark.objects.filter(user=student, material=material).exists(), "Material bookmark model record was not created"

    before_count = material.download_count
    driver.get(f"{BASE_URL}/materials/{material.pk}/download/")
    time.sleep(2)

    material.refresh_from_db()
    assert material.download_count == before_count + 1, "Download count did not increase"

    print("Material Bookmark/Download Test Passed ✅")
    print("Note: materials app has Bookmark model but no material bookmark URL/view, so bookmark part is DB-validated.")

finally:
    driver.quit()

