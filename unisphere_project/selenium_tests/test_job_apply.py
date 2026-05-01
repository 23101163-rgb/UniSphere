import os
import sys
from datetime import timedelta

# Add project root to Python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "unisphere.settings")

import django
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone

from jobs.models import JobListing, JobApplication

from common import get_driver, login, BASE_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


User = get_user_model()


def get_or_create_user(username, password, role, email):
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "role": role,
            "department": "CSE",
        }
    )

    user.email = email
    user.role = role
    user.department = "CSE"
    user.set_password(password)
    user.save()

    return user


# Create stable test users
poster = get_or_create_user(
    username="selenium_job_poster",
    password="TestPass123@#",
    role="admin",
    email="poster@test.com"
)

applicant = get_or_create_user(
    username="selenium_job_applicant",
    password="TestPass123@#",
    role="student",
    email="applicant@test.com"
)

# Create stable verified running job
job = JobListing.objects.create(
    title="Selenium Test Job Apply",
    company_name="Selenium Company",
    job_type="internship",
    description="This is a Selenium test job.",
    required_skills="Python, Django, Selenium",
    eligibility="CSE students",
    salary_range="10000-15000",
    application_deadline=timezone.now().date() + timedelta(days=30),
    application_link="https://example.com/apply",
    posted_by=poster,
    is_verified=True,
)

# Make sure this applicant has not already applied to this new job
JobApplication.objects.filter(job=job, applicant=applicant).delete()


driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    # Step 1: Login as applicant
    login(driver, "selenium_job_applicant", "TestPass123@#")

    wait.until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Step 2: Go directly to apply page
    driver.get(f"{BASE_URL}/jobs/{job.pk}/apply/")

    wait.until(
        EC.presence_of_element_located((By.NAME, "full_name"))
    )

    print("Job Apply Form Loaded ✅")

    # Step 3: Fill application form
    full_name = driver.find_element(By.NAME, "full_name")
    full_name.clear()
    full_name.send_keys("Selenium Applicant")

    email = driver.find_element(By.NAME, "email")
    email.clear()
    email.send_keys("applicant@test.com")

    phone = driver.find_element(By.NAME, "phone")
    phone.clear()
    phone.send_keys("01700000000")

    cover_letter = driver.find_element(By.NAME, "cover_letter")
    cover_letter.clear()
    cover_letter.send_keys("I am interested in this internship.")

    cv_link = driver.find_element(By.NAME, "cv_link")
    cv_link.clear()
    cv_link.send_keys("https://example.com/cv")

    # Step 4: Submit form
    driver.find_element(By.TAG_NAME, "form").submit()

    wait.until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Step 5: Confirm application saved in database
    application_exists = JobApplication.objects.filter(
        job=job,
        applicant=applicant
    ).exists()

    assert application_exists, "Job application was not saved in database"

    print("Job Application Submitted ✅")
    print("Job Apply Test Passed ✅")

finally:
    driver.quit()
