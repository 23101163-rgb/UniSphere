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


# Setup: create a verified job listing
poster = ensure_user("selenium_job_poster", role="teacher")
viewer = ensure_user("selenium_job_viewer", role="student")

UNIQUE_TITLE = "SeleniumJobDetail_XYZ777"
JobListing.objects.filter(title=UNIQUE_TITLE).delete()

job = JobListing.objects.create(
    title=UNIQUE_TITLE,
    company_name="Selenium Test Corp",
    job_type="job",
    description="This is a Selenium test job for detail page verification.",
    required_skills="Python, Django, Selenium",
    eligibility="CSE Students",
    salary_range="50,000 - 80,000 BDT",
    application_deadline=date.today() + timedelta(days=30),
    application_link="https://example.com/apply",
    posted_by=poster,
    is_verified=True,
)

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    # Step 1: Login as student
    login(driver, "selenium_job_viewer", PASSWORD)

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Step 2: Navigate to job detail page
    driver.get(f"{BASE_URL}/jobs/{job.pk}/")

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    assert f"/jobs/{job.pk}" in driver.current_url, (
        f"Job detail page did not load.\nURL: {driver.current_url}"
    )

    print("Job Detail Page Loaded ✅")

    # Step 3: Verify job details appear on page
    page_source = driver.page_source

    assert UNIQUE_TITLE in page_source, (
        f"Job title '{UNIQUE_TITLE}' not found on detail page."
    )

    print("Job Title Visible ✅")

    assert "Selenium Test Corp" in page_source, (
        "Company name not found on job detail page."
    )

    print("Company Name Visible ✅")

    assert "Python" in page_source or "Django" in page_source, (
        "Required skills not found on job detail page."
    )

    print("Required Skills Visible ✅")

    # Step 4: Verify the Apply button/link is present
    apply_present = (
        "apply" in page_source.lower()
        or "example.com/apply" in page_source
    )
    assert apply_present, (
        "Apply link/button not found on job detail page."
    )

    print("Apply Link Present ✅")
    print("Job Detail Page Test Passed ✅")

finally:
    # Cleanup
    job.delete()
    driver.quit()
