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
from events.models import Event, EventRegistration

PASSWORD = "TestPass123@#"

creator = ensure_user(
    username="selenium_event_cancel_creator",
    password=PASSWORD,
    role="teacher",
    email="selenium_event_cancel_creator@uap-bd.edu",
    first_name="Cancel",
    last_name="Creator",
)

student = ensure_user(
    username="selenium_event_cancel_student",
    password=PASSWORD,
    role="student",
    email="selenium_event_cancel_student@uap-bd.edu",
    first_name="Cancel",
    last_name="Student",
    phone="01712345678",
)

Event.objects.filter(title="Selenium Cancel Registration Event").delete()

event = Event.objects.create(
    title="Selenium Cancel Registration Event",
    description="Approved event for cancel registration test.",
    event_type="training",
    organizer_category="non_club",
    club_name="",
    date=timezone.localdate() + timedelta(days=25),
    time="11:00",
    venue="Room 501",
    registration_link="",
    created_by=creator,
    is_approved=True,
)

EventRegistration.objects.update_or_create(
    event=event,
    user=student,
    defaults={
        "full_name": "Cancel Student",
        "email": student.email,
        "phone": "01712345678",
        "department": "CSE",
        "university_id": student.university_id,
        "note": "Already registered for cancel test",
    },
)

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    login(driver, "selenium_event_cancel_student", PASSWORD)

    driver.get(f"{BASE_URL}/events/{event.pk}/")
    wait_page_ready(driver)

    assert EventRegistration.objects.filter(event=event, user=student).exists(), "Pre-created registration missing"

    driver.get(f"{BASE_URL}/events/{event.pk}/register/")
    wait_page_ready(driver)

    assert not EventRegistration.objects.filter(event=event, user=student).exists(), "Registration was not cancelled"

    print("Event Cancel Registration Test Passed ✅")

finally:
    driver.quit()

