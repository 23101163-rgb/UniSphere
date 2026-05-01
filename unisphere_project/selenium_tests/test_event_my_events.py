import os
import sys
from datetime import date, time as dtime, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "unisphere.settings")

import django
django.setup()

from django.contrib.auth import get_user_model

from events.models import Event, EventRegistration

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


# Setup
teacher = ensure_user("selenium_myev_teacher", role="teacher")
student = ensure_user("selenium_myev_student", role="student")

# Fresh event + registration
Event.objects.filter(title="Selenium My Events Test").delete()
event = Event.objects.create(
    title="Selenium My Events Test",
    description="Event for my-events page test.",
    event_type="seminar",
    organizer_category="non_club",
    date=date.today() + timedelta(days=10),
    time=dtime(14, 0),
    venue="Auditorium",
    registration_link="https://example.com/event",
    created_by=teacher,
    is_approved=True,
)

# Register the student for this event
EventRegistration.objects.get_or_create(
    event=event,
    user=student,
    defaults={
        "full_name": "Selenium Student",
        "email": student.email,
        "phone": "01700000000",
        "department": "CSE",
        "university_id": student.university_id,
    },
)

driver = get_driver()

try:
    # Step 1: Login as the registered student
    login(driver, "selenium_myev_student", PASSWORD)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Step 2: Open My Events page
    driver.get(f"{BASE_URL}/events/my-events/")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    print("My Events URL:", driver.current_url)

    page_text = driver.page_source

    # Step 3: The registered event should appear
    assert "Selenium My Events Test" in page_text, (
        f"Registered event not shown on My Events page.\n"
        f"URL: {driver.current_url}\n"
        f"Preview: {page_text[:1000]}"
    )

    print("My Events Page Test Passed ✅")

finally:
    driver.quit()

