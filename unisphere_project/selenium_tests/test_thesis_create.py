import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "unisphere.settings")

import django
django.setup()

from django.contrib.auth import get_user_model
from thesis.models import ThesisResource

from common import get_driver, login, BASE_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

User = get_user_model()
PASSWORD = "TestPass123@#"


def ensure_user(username, role="teacher"):
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


# Setup
teacher = ensure_user("selenium_thesis_creator", role="teacher")

UNIQUE_TITLE = "SeleniumThesis_UniqueABC999"
ThesisResource.objects.filter(title=UNIQUE_TITLE).delete()

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    # Step 1: Login as teacher
    login(driver, "selenium_thesis_creator", PASSWORD)

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Step 2: Navigate to thesis creation page
    driver.get(f"{BASE_URL}/thesis/create/")

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    print("Thesis Create Page Loaded ✅")

    # Step 3: Fill in the thesis form
    title_field = wait.until(EC.presence_of_element_located((By.NAME, "title")))
    title_field.clear()
    title_field.send_keys(UNIQUE_TITLE)

    abstract_field = driver.find_element(By.NAME, "abstract")
    abstract_field.clear()
    abstract_field.send_keys("This is a test abstract for Selenium thesis creation test.")

    authors_field = driver.find_element(By.NAME, "authors")
    authors_field.clear()
    authors_field.send_keys("Selenium Test Author, Test Co-Author")

    year_field = driver.find_element(By.NAME, "year")
    year_field.clear()
    year_field.send_keys("2025")

    research_area_field = driver.find_element(By.NAME, "research_area")
    research_area_field.clear()
    research_area_field.send_keys("Machine Learning")

    # Step 4: Submit the form
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    wait.until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

    # Step 5: Verify thesis was created in DB
    thesis_exists = ThesisResource.objects.filter(title=UNIQUE_TITLE).exists()
    assert thesis_exists, (
        f"Thesis '{UNIQUE_TITLE}' was not found in database after submission.\n"
        f"URL: {driver.current_url}"
    )

    print("Thesis Created in Database ✅")
    print("Thesis Create Test Passed ✅")

finally:
    # Cleanup
    ThesisResource.objects.filter(title=UNIQUE_TITLE).delete()
    driver.quit()
