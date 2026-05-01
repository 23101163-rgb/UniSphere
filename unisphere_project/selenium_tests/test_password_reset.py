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

ensure_user(
    username="selenium_reset_user",
    password=PASSWORD,
    role="student",
    email="selenium_reset_user@uap-bd.edu",
    first_name="Reset",
    last_name="User",
)

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    driver.get(f"{BASE_URL}/accounts/password-reset/")
    wait.until(EC.presence_of_element_located((By.NAME, "email")))

    email_input = driver.find_element(By.NAME, "email")
    email_input.clear()
    email_input.send_keys("selenium_reset_user@uap-bd.edu")

    driver.find_element(By.TAG_NAME, "form").submit()

    wait.until(EC.url_contains("/accounts/password-reset/done/"))
    wait_page_ready(driver)

    page_text = driver.page_source.lower()
    assert "reset" in page_text or "password" in page_text, "Password reset done page did not show expected text"

    print("Password Reset Request Test Passed ✅")

finally:
    driver.quit()

