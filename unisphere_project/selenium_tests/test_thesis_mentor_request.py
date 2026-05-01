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
from thesis.models import MentorshipRequest

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


def wait_for_mentorship_request(student, mentor, topic, timeout=10):
    for _ in range(timeout * 2):
        if MentorshipRequest.objects.filter(
            student=student,
            mentor=mentor,
            topic=topic,
            status="pending"
        ).exists():
            return True
        time.sleep(0.5)

    return False


ADIKA_PASSWORD = "amiadika123@#"
NMK_PASSWORD = "amiarnob123@#"
TOPIC = "Selenium Thesis Mentor Topic"

mentor = ensure_user(
    username="NMK",
    password=NMK_PASSWORD,
    role="teacher",
    email="arnob@uap-bd.edu",
    first_name="NMK",
    last_name="Arnob",
    university_id="00987",
    is_mentor_available=True,
)

student = ensure_user(
    username="Adika",
    password=ADIKA_PASSWORD,
    role="student",
    email="23101162@uap-bd.edu",
    first_name="Adika",
    last_name="Sulatana",
    university_id="23101162",
)

MentorshipRequest.objects.filter(
    student=student,
    mentor=mentor,
    topic=TOPIC
).delete()

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    login(driver, "Adika", ADIKA_PASSWORD)

    driver.get(f"{BASE_URL}/thesis/mentors/")
    wait_page_ready(driver)

    page_text = driver.page_source.lower()
    assert (
        "nmk" in page_text or
        "arnob" in page_text or
        "mentor" in page_text
    ), "Mentor list did not load expected mentor"

    driver.get(f"{BASE_URL}/thesis/mentors/{mentor.pk}/request/")
    wait_page_ready(driver)

    topic_field = wait.until(
        EC.presence_of_element_located((By.NAME, "topic"))
    )
    topic_field.clear()
    topic_field.send_keys(TOPIC)

    message_field = driver.find_element(By.NAME, "message")
    message_field.clear()
    message_field.send_keys("Please guide me on this thesis topic.")

    form = driver.find_element(By.TAG_NAME, "form")
    form.submit()

    wait_page_ready(driver)

    assert wait_for_mentorship_request(
        student=student,
        mentor=mentor,
        topic=TOPIC,
        timeout=10
    ), "Mentorship request was not created"

    print("Thesis Mentor Request Test Passed ✅")

finally:
    driver.quit()
