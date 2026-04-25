import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "unilink.settings")

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


from selenium.webdriver.support.ui import Select
from research.models import ResearchGroup, SupervisorRequest
from notifications.models import Notification

PASSWORD = "TestPass123@#"

supervisor = ensure_user(
    username="selenium_supervisor_teacher",
    password=PASSWORD,
    role="teacher",
    email="selenium_supervisor_teacher@uap-bd.edu",
    first_name="Main",
    last_name="Supervisor",
)

cosupervisor = ensure_user(
    username="selenium_cosupervisor_teacher",
    password=PASSWORD,
    role="teacher",
    email="selenium_cosupervisor_teacher@uap-bd.edu",
    first_name="Co",
    last_name="Supervisor",
)

leader = ensure_user(
    username="selenium_cosupervisor_leader",
    password=PASSWORD,
    role="student",
    email="selenium_cosupervisor_leader@uap-bd.edu",
    first_name="Research",
    last_name="Leader",
)

ResearchGroup.objects.filter(name="Selenium CoSupervisor Group").delete()

group = ResearchGroup.objects.create(
    name="Selenium CoSupervisor Group",
    description="Active group for co-supervisor request test.",
    research_area="Computer Vision",
    group_type="open",
    created_by=leader,
    supervisor=supervisor,
    status="active",
)
group.members.add(leader)

SupervisorRequest.objects.filter(group=group, faculty=cosupervisor, request_type="co_supervisor").delete()
Notification.objects.filter(recipient=cosupervisor, title="New Co-Supervisor Request").delete()

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    login(driver, "selenium_supervisor_teacher", PASSWORD)

    driver.get(f"{BASE_URL}/research/groups/{group.pk}/request-cosupervisor/")
    wait_page_ready(driver)

    Select(wait.until(EC.presence_of_element_located((By.NAME, "faculty")))).select_by_value(str(cosupervisor.pk))

    message = driver.find_element(By.NAME, "message")
    message.clear()
    message.send_keys("Please join as co-supervisor for Selenium test.")

    driver.find_element(By.TAG_NAME, "form").submit()
    wait_page_ready(driver)

    assert SupervisorRequest.objects.filter(
        group=group,
        faculty=cosupervisor,
        request_type="co_supervisor",
        status="pending"
    ).exists(), "Co-supervisor request was not created"

    assert Notification.objects.filter(
        recipient=cosupervisor,
        title="New Co-Supervisor Request",
        link="/research/supervisor-requests/"
    ).exists(), "Co-supervisor notification was not created"

    driver.get(f"{BASE_URL}/accounts/logout/")
    login(driver, "selenium_cosupervisor_teacher", PASSWORD)

    driver.get(f"{BASE_URL}/research/supervisor-requests/")
    wait_page_ready(driver)

    page_text = driver.page_source.lower()
    assert "selenium cosupervisor group" in page_text, "Co-supervisor request not visible to teacher"
    assert "co-supervisor" in page_text, "Request type not shown as co-supervisor"

    print("Co-Supervisor Request Notification Test Passed ✅")

finally:
    driver.quit()
