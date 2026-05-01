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
from materials.models import StudyMaterial

PASSWORD = "TestPass123@#"

teacher = ensure_user(
    username="selenium_material_teacher",
    password=PASSWORD,
    role="teacher",
    email="selenium_material_teacher@uap-bd.edu",
    first_name="Material",
    last_name="Teacher",
)

student = ensure_user(
    username="selenium_material_browser",
    password=PASSWORD,
    role="student",
    email="selenium_material_browser@uap-bd.edu",
    first_name="Material",
    last_name="Browser",
)

StudyMaterial.objects.filter(title="Selenium AI Notes").delete()

material = StudyMaterial(
    title="Selenium AI Notes",
    description="Artificial Intelligence notes for Selenium browsing test.",
    course_name="CSE101",
    semester="1.1",
    topic="AI Basics",
    tags="AI, Selenium, Test",
    uploaded_by=teacher,
    is_approved=True,
)
material.file.save("selenium_ai_notes.txt", ContentFile(b"Selenium AI material content"), save=True)

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    login(driver, "selenium_material_browser", PASSWORD)

    driver.get(f"{BASE_URL}/materials/semester/1.1/course/CSE101/?q=AI")
    wait_page_ready(driver)

    assert "selenium ai notes" in driver.page_source.lower(), "Material search result did not show the created material"

    driver.get(f"{BASE_URL}/materials/{material.pk}/")
    wait_page_ready(driver)

    page_text = driver.page_source.lower()
    assert "selenium ai notes" in page_text, "Material detail page did not load"
    assert "ai basics" in page_text or "artificial intelligence" in page_text, "Material detail content missing"

    print("Material Browse/Search Test Passed ✅")

finally:
    driver.quit()

