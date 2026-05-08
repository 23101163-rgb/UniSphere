import os
import sys
import time

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


# Create uploader user
uploader = ensure_user("selenium_mat_editor", role="teacher")

ORIGINAL_TITLE = "SeleniumMaterialEdit_Original"
UPDATED_TITLE = "SeleniumMaterialEdit_Updated999"

# Cleanup old test materials
StudyMaterial.objects.filter(
    title__in=[ORIGINAL_TITLE, UPDATED_TITLE]
).delete()

# Create dummy file
dummy_file = SimpleUploadedFile(
    "test.pdf",
    b"Dummy PDF content",
    content_type="application/pdf"
)

# Create material
material = StudyMaterial.objects.create(
    title=ORIGINAL_TITLE,
    description="Original description before edit.",
    course_name="CSE9999",
    semester="1.1",
    topic="Selenium Testing",
    tags="selenium,test",
    uploaded_by=uploader,
    is_approved=True,
    file=dummy_file,
)

material_pk = material.pk

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    # Step 1: Login
    login(driver, "selenium_mat_editor", PASSWORD)

    wait.until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Step 2: Open edit page
    driver.get(f"{BASE_URL}/materials/{material_pk}/edit/")

    wait.until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    print("Material Edit Page Loaded ✅")

    # Step 3: Update title
    title_field = wait.until(
        EC.presence_of_element_located((By.NAME, "title"))
    )

    title_field.clear()
    title_field.send_keys(UPDATED_TITLE)

    # Step 4: Update description
    desc_field = driver.find_element(By.NAME, "description")

    desc_field.clear()

    desc_field.send_keys(
        "Updated description after Selenium edit test."
    )

    # Step 5: Find submit button
    submit_button = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//button[@type='submit']")
        )
    )

    # Scroll to submit button
    driver.execute_script(
        "arguments[0].scrollIntoView(true);",
        submit_button
    )

    time.sleep(1)

    # JavaScript click
    driver.execute_script(
        "arguments[0].click();",
        submit_button
    )

    # Wait after submit
    time.sleep(3)

    print("Current URL:", driver.current_url)

    # Print validation errors if any
    errors = driver.find_elements(By.CLASS_NAME, "errorlist")

    if errors:
        print("\nFORM ERRORS:")
        for err in errors:
            print(err.text)

    # Refresh material from DB
    material.refresh_from_db()

    print("Database Title:", material.title)

    # Verify update
    assert material.title == UPDATED_TITLE, (
        f"Title was not updated.\n"
        f"Expected: {UPDATED_TITLE}\n"
        f"Got: {material.title}"
    )

    print("Material Title Updated in DB ✅")
    print("Material Edit Test Passed ✅")

finally:
    # Cleanup
    StudyMaterial.objects.filter(pk=material_pk).delete()

    driver.quit()