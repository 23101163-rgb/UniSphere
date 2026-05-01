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


from thesis.models import MentorshipRequest

PASSWORD = "TestPass123@#"

mentor = ensure_user(
    username="selenium_thesis_mentor",
    password=PASSWORD,
    role="teacher",
    email="selenium_thesis_mentor@uap-bd.edu",
    first_name="Thesis",
    last_name="Mentor",
    is_mentor_available=True,
    research_interests="AI, Machine Learning",
    expertise="Research Supervision",
)

student = ensure_user(
    username="selenium_thesis_student",
    password=PASSWORD,
    role="student",
    email="selenium_thesis_student@uap-bd.edu",
    first_name="Thesis",
    last_name="Student",
)

MentorshipRequest.objects.filter(student=student, mentor=mentor, topic="Selenium Thesis Mentor Topic").delete()

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    login(driver, "selenium_thesis_student", PASSWORD)

    driver.get(f"{BASE_URL}/thesis/mentors/")
    wait_page_ready(driver)
    assert "thesis mentor" in driver.page_source.lower() or "selenium_thesis_mentor" in driver.page_source.lower(), "Mentor list did not load expected mentor"

    driver.get(f"{BASE_URL}/thesis/mentors/{mentor.pk}/request/")
    wait_page_ready(driver)

    topic = wait.until(EC.presence_of_element_located((By.NAME, "topic")))
    topic.clear()
    topic.send_keys("Selenium Thesis Mentor Topic")

    message = driver.find_element(By.NAME, "message")
    message.clear()
    message.send_keys("Please guide me on this thesis topic.")

    driver.find_element(By.TAG_NAME, "form").submit()
    wait.until(EC.url_contains("/thesis/mentors"))
    wait_page_ready(driver)

    assert MentorshipRequest.objects.filter(
        student=student,
        mentor=mentor,
        topic="Selenium Thesis Mentor Topic",
        status="pending"
    ).exists(), "Mentorship request was not created"

    print("Thesis Mentor Request Test Passed ✅")

finally:
    driver.quit()

