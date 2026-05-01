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


PASSWORD = "TestPass123@#"

user = ensure_user(
    username="selenium_profile_user",
    password=PASSWORD,
    role="student",
    email="selenium_profile_user@uap-bd.edu",
    first_name="Old",
    last_name="Name",
    phone="01000000000",
    bio="Old bio",
)

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    login(driver, "selenium_profile_user", PASSWORD)

    driver.get(f"{BASE_URL}/accounts/profile/edit/")
    wait_page_ready(driver)

    updates = {
        "first_name": "Selenium",
        "last_name": "Profile",
        "phone": "01711112222",
        "bio": "Updated by Selenium profile test.",
        "semester": "4.2",
        "research_interests": "Artificial Intelligence, Software Testing",
        "expertise": "Django Selenium",
    }

    for name, value in updates.items():
        field = wait.until(EC.presence_of_element_located((By.NAME, name)))
        field.clear()
        field.send_keys(value)

    driver.find_element(By.TAG_NAME, "form").submit()
    wait.until(EC.url_contains("/accounts/profile"))
    wait_page_ready(driver)

    user.refresh_from_db()
    assert user.first_name == "Selenium", "First name was not updated"
    assert user.last_name == "Profile", "Last name was not updated"
    assert user.phone == "01711112222", "Phone was not updated"
    assert "Updated by Selenium" in user.bio, "Bio was not updated"
    assert "Artificial Intelligence" in user.research_interests, "Research interests were not updated"

    print("Profile Update Test Passed ✅")

finally:
    driver.quit()

