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


from django.core.files.base import ContentFile
from research.models import ResearchGroup, ResearchPaper, PaperReview

PASSWORD = "TestPass123@#"

member = ensure_user(
    username="selenium_paper_member",
    password=PASSWORD,
    role="student",
    email="selenium_paper_member@uap-bd.edu",
    first_name="Paper",
    last_name="Member",
)

supervisor = ensure_user(
    username="selenium_paper_supervisor",
    password=PASSWORD,
    role="teacher",
    email="selenium_paper_supervisor@uap-bd.edu",
    first_name="Paper",
    last_name="Supervisor",
)

cosupervisor = ensure_user(
    username="selenium_paper_cosupervisor",
    password=PASSWORD,
    role="teacher",
    email="selenium_paper_cosupervisor@uap-bd.edu",
    first_name="Paper",
    last_name="CoSupervisor",
)

ResearchGroup.objects.filter(name="Selenium Paper Workflow Group").delete()

group = ResearchGroup.objects.create(
    name="Selenium Paper Workflow Group",
    description="Group for complete paper workflow Selenium test.",
    research_area="NLP",
    research_topic="Selenium Research Automation",
    group_type="open",
    created_by=member,
    supervisor=supervisor,
    co_supervisor=cosupervisor,
    status="paper_writing",
)
group.members.add(member)

paper_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "selenium_test_paper.txt")
with open(paper_file_path, "w", encoding="utf-8") as f:
    f.write("Selenium research paper content")

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    login(driver, "selenium_paper_member", PASSWORD)

    driver.get(f"{BASE_URL}/research/groups/{group.pk}/submit-paper/")
    wait_page_ready(driver)

    title = wait.until(EC.presence_of_element_located((By.NAME, "title")))
    title.clear()
    title.send_keys("Selenium Research Paper")

    abstract = driver.find_element(By.NAME, "abstract")
    abstract.clear()
    abstract.send_keys("This abstract is submitted by Selenium.")

    driver.find_element(By.NAME, "document").send_keys(paper_file_path)
    driver.find_element(By.TAG_NAME, "form").submit()
    wait_page_ready(driver)

    paper = ResearchPaper.objects.get(group=group, title="Selenium Research Paper")
    assert paper.status == "submitted", "Paper was not submitted for review"

    driver.get(f"{BASE_URL}/accounts/logout/")
    login(driver, "selenium_paper_supervisor", PASSWORD)

    driver.get(f"{BASE_URL}/research/paper/{paper.pk}/review/")
    wait_page_ready(driver)

    feedback = wait.until(EC.presence_of_element_located((By.NAME, "feedback")))
    feedback.clear()
    feedback.send_keys("Supervisor approved by Selenium.")

    approve_box = driver.find_element(By.NAME, "is_approved")
    if not approve_box.is_selected():
        approve_box.click()

    driver.find_element(By.TAG_NAME, "form").submit()
    wait_page_ready(driver)

    assert PaperReview.objects.filter(paper=paper, reviewer=supervisor, is_approved=True).exists(), "Supervisor review was not saved"

    driver.get(f"{BASE_URL}/accounts/logout/")
    login(driver, "selenium_paper_cosupervisor", PASSWORD)

    driver.get(f"{BASE_URL}/research/paper/{paper.pk}/review/")
    wait_page_ready(driver)

    feedback = wait.until(EC.presence_of_element_located((By.NAME, "feedback")))
    feedback.clear()
    feedback.send_keys("Co-supervisor approved by Selenium.")

    approve_box = driver.find_element(By.NAME, "is_approved")
    if not approve_box.is_selected():
        approve_box.click()

    driver.find_element(By.TAG_NAME, "form").submit()
    wait_page_ready(driver)

    paper.refresh_from_db()
    assert paper.status == "approved", "Paper was not approved after both reviews"

    driver.get(f"{BASE_URL}/accounts/logout/")
    login(driver, "selenium_paper_supervisor", PASSWORD)

    driver.get(f"{BASE_URL}/research/paper/{paper.pk}/publish/")
    wait_page_ready(driver)

    paper.refresh_from_db()
    group.refresh_from_db()

    assert paper.status == "published", "Paper was not published"
    assert group.status == "published", "Research group was not marked as published"

    print("Research Paper Workflow Test Passed ✅")

finally:
    driver.quit()
    if os.path.exists(paper_file_path):
        os.remove(paper_file_path)

