import os
import sys
from datetime import date, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "unisphere.settings")

import django
django.setup()

from django.contrib.auth import get_user_model

from jobs.models import JobListing

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


# Setup: poster (alumni) + admin
poster = ensure_user("selenium_job_poster_v", role="alumni")
admin = ensure_user("selenium_job_admin", role="admin")

# Create a fresh unverified job
JobListing.objects.filter(title="Selenium Verify Job").delete()

job = JobListing.objects.create(
    title="Selenium Verify Job",
    company_name="Test Co",
    job_type="job",
    description="Job created for verify test.",
    required_skills="Python, Django",
    eligibility="CSE students",
    salary_range="25000",
    application_deadline=date.today() + timedelta(days=15),
    application_link="https://example.com/apply",
    posted_by=poster,
    is_verified=False,
)

assert not job.is_verified, "Setup failed: job should be unverified"

driver = get_driver()

try:
    # Step 1: Login as admin
    login(driver, "selenium_job_admin", PASSWORD)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Step 2: Hit verify URL directly
    driver.get(f"{BASE_URL}/jobs/{job.pk}/verify/")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    print("After verify URL:", driver.current_url)

    # Step 3: Verify job is now verified in DB
    job.refresh_from_db()
    assert job.is_verified, (
        f"Job should be verified after admin action.\n"
        f"is_verified={job.is_verified}"
    )

    print("Job Verify Test Passed ✅")

finally:
    driver.quit()

