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
from notifications.models import Notification

PASSWORD = "TestPass123@#"

creator = ensure_user(
    username="selenium_pending_event_creator",
    password=PASSWORD,
    role="student",
    email="selenium_pending_event_creator@uap-bd.edu",
    first_name="Pending",
    last_name="Creator",
    is_club_member=False,
)

admin = ensure_user(
    username="selenium_event_admin",
    password=PASSWORD,
    role="admin",
    email="selenium_event_admin@uap-bd.edu",
    first_name="Event",
    last_name="Admin",
)

Event.objects.filter(title="Selenium Pending Event").delete()

event = Event.objects.create(
    title="Selenium Pending Event",
    description="Pending event for approval test.",
    event_type="seminar",
    organizer_category="non_club",
    club_name="",
    date=timezone.localdate() + timedelta(days=15),
    time="14:00",
    venue="Auditorium",
    registration_link="",
    created_by=creator,
    is_approved=False,
)

Notification.objects.filter(recipient=creator, title="Event Approved!").delete()

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    login(driver, "selenium_event_admin", PASSWORD)

    driver.get(f"{BASE_URL}/events/pending/")
    wait_page_ready(driver)

    assert "selenium pending event" in driver.page_source.lower(), "Pending event was not visible on pending page"

    driver.get(f"{BASE_URL}/events/{event.pk}/approve/")
    wait_page_ready(driver)

    event.refresh_from_db()
    assert event.is_approved is True, "Event was not approved"

    assert Notification.objects.filter(
        recipient=creator,
        title="Event Approved!",
        link=f"/events/{event.pk}/"
    ).exists(), "Event approval notification was not created"

    print("Event Approval Flow Test Passed ✅")

finally:
    driver.quit()

