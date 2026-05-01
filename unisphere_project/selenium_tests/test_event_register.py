import os
import sys
import time
from datetime import date, time as dt_time, timedelta

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
from events.models import Event, EventRegistration

User = get_user_model()


def ensure_user(username, password, role="student", email=None, **extra):
    email = email or f"{username}@uap-bd.edu"

    user, _ = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "role": role,
            "department": "CSE",
            "university_id": extra.pop(
                "university_id",
                f"U{abs(hash(username)) % 1000000:06d}"
            ),
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


def set_if_present(driver, name, value):
    elements = driver.find_elements(By.NAME, name)
    if not elements:
        return False

    field = elements[0]
    tag = field.tag_name.lower()

    if tag == "select":
        from selenium.webdriver.support.ui import Select
        Select(field).select_by_value(value)
    else:
        field.clear()
        field.send_keys(value)

    return True


def wait_for_registration(event, user, timeout=10):
    for _ in range(timeout * 2):
        if EventRegistration.objects.filter(event=event, user=user).exists():
            return True
        time.sleep(0.5)

    return False


ADIKA_PASSWORD = "amiadika123@#"
NMK_PASSWORD = "amiarnob123@#"

student = ensure_user(
    username="Adika",
    password=ADIKA_PASSWORD,
    role="student",
    email="23101162@uap-bd.edu",
    first_name="Adika",
    last_name="Sulatana",
    university_id="23101162",
)

teacher = ensure_user(
    username="NMK",
    password=NMK_PASSWORD,
    role="teacher",
    email="arnob@uap-bd.edu",
    first_name="NMK",
    last_name="Arnob",
    university_id="00987",
)

event = Event.objects.create(
    title="Selenium Event Registration Test",
    description="Selenium event registration description",
    organizer_category="non_club",
    club_name="",
    event_type="seminar",
    date=date.today() + timedelta(days=7),
    time=dt_time(10, 30),
    venue="Room 101",
    registration_link="",
    created_by=teacher,
    is_approved=True,
)

EventRegistration.objects.filter(event=event, user=student).delete()

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    login(driver, "Adika", ADIKA_PASSWORD)

    driver.get(f"{BASE_URL}/events/{event.pk}/register/")
    wait_page_ready(driver)

    set_if_present(driver, "full_name", "Adika Sulatana")
    set_if_present(driver, "email", "23101162@uap-bd.edu")
    set_if_present(driver, "phone", "01700000000")
    set_if_present(driver, "department", "CSE")
    set_if_present(driver, "university_id", "23101162")
    set_if_present(driver, "note", "Selenium registration test")

    form = wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
    form.submit()

    wait_page_ready(driver)

    assert wait_for_registration(event, student), (
        "Registration failed.\n"
        f"URL: {driver.current_url}\n"
        f"Preview: {driver.page_source[:800].lower()}"
    )

    print("Event Register Test Passed ✅")

finally:
    driver.quit()