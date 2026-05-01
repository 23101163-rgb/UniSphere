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
from jobs.models import JobListing, JobBookmark

PASSWORD = "TestPass123@#"

poster = ensure_user(
    username="selenium_job_search_poster",
    password=PASSWORD,
    role="admin",
    email="selenium_job_search_poster@uap-bd.edu",
    first_name="Job",
    last_name="Poster",
)

student = ensure_user(
    username="selenium_job_search_student",
    password=PASSWORD,
    role="student",
    email="selenium_job_search_student@uap-bd.edu",
    first_name="Job",
    last_name="Searcher",
)

JobListing.objects.filter(title="Selenium Django Internship").delete()

job = JobListing.objects.create(
    title="Selenium Django Internship",
    company_name="Selenium Tech",
    job_type="internship",
    description="Internship for Django Selenium testing.",
    required_skills="Python, Django, Selenium",
    eligibility="CSE students",
    salary_range="10000-15000",
    application_deadline=timezone.now().date() + timedelta(days=30),
    application_link="https://example.com/apply",
    posted_by=poster,
    is_verified=True,
)

JobBookmark.objects.filter(user=student, job=job).delete()

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    login(driver, "selenium_job_search_student", PASSWORD)

    driver.get(f"{BASE_URL}/jobs/?q=Django&type=internship")
    wait_page_ready(driver)

    assert "selenium django internship" in driver.page_source.lower(), "Job search result did not show created job"

    driver.get(f"{BASE_URL}/jobs/{job.pk}/bookmark/")
    wait_page_ready(driver)

    assert JobBookmark.objects.filter(user=student, job=job).exists(), "Job was not bookmarked"

    driver.get(f"{BASE_URL}/jobs/bookmarks/")
    wait_page_ready(driver)

    assert "selenium django internship" in driver.page_source.lower(), "Bookmarked job was not visible in saved jobs page"

    print("Job Search/Bookmark Test Passed ✅")

finally:
    driver.quit()

