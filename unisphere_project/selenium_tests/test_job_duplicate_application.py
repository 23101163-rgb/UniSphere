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
from jobs.models import JobListing, JobApplication

PASSWORD = "TestPass123@#"

poster = ensure_user(
    username="selenium_duplicate_job_poster",
    password=PASSWORD,
    role="admin",
    email="selenium_duplicate_job_poster@uap-bd.edu",
    first_name="Duplicate",
    last_name="Poster",
)

student = ensure_user(
    username="selenium_duplicate_job_student",
    password=PASSWORD,
    role="student",
    email="selenium_duplicate_job_student@uap-bd.edu",
    first_name="Duplicate",
    last_name="Applicant",
    phone="01799998888",
)

JobListing.objects.filter(title="Selenium Duplicate Application Job").delete()

job = JobListing.objects.create(
    title="Selenium Duplicate Application Job",
    company_name="Duplicate Ltd",
    job_type="job",
    description="Job for duplicate application test.",
    required_skills="Django, Testing",
    eligibility="CSE students",
    salary_range="25000",
    application_deadline=timezone.now().date() + timedelta(days=30),
    application_link="https://example.com/apply",
    posted_by=poster,
    is_verified=True,
)

JobApplication.objects.update_or_create(
    job=job,
    applicant=student,
    defaults={
        "full_name": "Duplicate Applicant",
        "email": student.email,
        "phone": "01799998888",
        "cover_letter": "First application.",
        "cv_link": "https://example.com/cv",
    },
)

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    login(driver, "selenium_duplicate_job_student", PASSWORD)

    driver.get(f"{BASE_URL}/jobs/{job.pk}/apply/")
    wait.until(EC.url_contains(f"/jobs/{job.pk}/"))
    wait_page_ready(driver)

    application_count = JobApplication.objects.filter(job=job, applicant=student).count()
    assert application_count == 1, f"Duplicate application allowed. Count: {application_count}"

    page_text = driver.page_source.lower()
    assert "already applied" in page_text or "selenium duplicate application job" in page_text, "Duplicate application warning/detail page not shown"

    print("Job Duplicate Application Prevention Test Passed ✅")

finally:
    driver.quit()

