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


from datetime import timedelta
from django.utils import timezone
from events.models import Event

PASSWORD = "TestPass123@#"

creator = ensure_user(
    username="selenium_event_filter_creator",
    password=PASSWORD,
    role="teacher",
    email="selenium_event_filter_creator@uap-bd.edu",
    first_name="Event",
    last_name="Creator",
)

student = ensure_user(
    username="selenium_event_filter_student",
    password=PASSWORD,
    role="student",
    email="selenium_event_filter_student@uap-bd.edu",
    first_name="Event",
    last_name="Viewer",
)

Event.objects.filter(title="Selenium Club Workshop").delete()

event = Event.objects.create(
    title="Selenium Club Workshop",
    description="A workshop created for Selenium event filter test.",
    event_type="workshop",
    organizer_category="club",
    club_name="software_hardware_club",
    date=timezone.localdate() + timedelta(days=20),
    time="10:30",
    venue="UAP Lab",
    registration_link="https://example.com/register",
    created_by=creator,
    is_approved=True,
)

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    login(driver, "selenium_event_filter_student", PASSWORD)

    driver.get(f"{BASE_URL}/events/")
    wait_page_ready(driver)

    assert "software and hardware club" in driver.page_source.lower(), "Club card/filter category was not visible"

    driver.get(f"{BASE_URL}/events/club/software_hardware_club/")
    wait_page_ready(driver)

    assert "selenium club workshop" in driver.page_source.lower(), "Filtered club event page did not show event"

    driver.get(f"{BASE_URL}/events/{event.pk}/")
    wait_page_ready(driver)

    page_text = driver.page_source.lower()
    assert "selenium club workshop" in page_text, "Event detail page did not load"
    assert "uap lab" in page_text, "Event venue missing from detail page"

    print("Event Filter/Detail Test Passed ✅")

finally:
    driver.quit()

