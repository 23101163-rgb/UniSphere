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
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from common import get_driver, login, BASE_URL
from research.models import ResearchGroup, SupervisorRequest
from notifications.models import Notification

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


def wait_for_supervisor_request(group, faculty, timeout=10):
    for _ in range(timeout * 2):
        if SupervisorRequest.objects.filter(
            group=group,
            faculty=faculty,
            request_type="co_supervisor",
            status="pending"
        ).exists():
            return True

        time.sleep(0.5)

    return False


def wait_for_notification(user, timeout=10):
    for _ in range(timeout * 2):
        if Notification.objects.filter(
            recipient=user,
            title="New Co-Supervisor Request",
            link="/research/supervisor-requests/"
        ).exists():
            return True

        time.sleep(0.5)

    return False


def collect_page_errors(driver):
    selectors = [
        ".alert",
        ".text-danger",
        ".text-warning",
        ".invalid-feedback",
        ".errorlist",
        ".help-block",
    ]

    messages = []

    for selector in selectors:
        for element in driver.find_elements(By.CSS_SELECTOR, selector):
            text = element.text.strip()
            if text:
                messages.append(text)

    return "\n".join(messages)


NMK_PASSWORD = "amiarnob123@#"
COSUPERVISOR_PASSWORD = "amicosupervisor123@#"

supervisor = ensure_user(
    username="NMK",
    password=NMK_PASSWORD,
    role="teacher",
    email="arnob@uap-bd.edu",
    first_name="NMK",
    last_name="Arnob",
    university_id="920001",
)

cosupervisor = ensure_user(
    username="SeleniumCoSupervisor",
    password=COSUPERVISOR_PASSWORD,
    role="teacher",
    email="selenium_cosupervisor@uap-bd.edu",
    first_name="Co",
    last_name="Supervisor",
    university_id="920009",
)

leader = ensure_user(
    username="Adika",
    password="amiadika123@#",
    role="student",
    email="23101162@uap-bd.edu",
    first_name="Adika",
    last_name="Sulatana",
    university_id="23101162",
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

SupervisorRequest.objects.filter(
    group=group,
    faculty=cosupervisor,
    request_type="co_supervisor"
).delete()

Notification.objects.filter(
    recipient=cosupervisor,
    title="New Co-Supervisor Request"
).delete()

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    login(driver, "NMK", NMK_PASSWORD)

    driver.get(f"{BASE_URL}/research/groups/{group.pk}/request-cosupervisor/")
    wait_page_ready(driver)

    faculty_select = wait.until(
        EC.presence_of_element_located((By.NAME, "faculty"))
    )
    Select(faculty_select).select_by_value(str(cosupervisor.pk))

    message = driver.find_element(By.NAME, "message")
    message.clear()
    message.send_keys("Please join as co-supervisor for Selenium test.")

    submit_buttons = driver.find_elements(
        By.CSS_SELECTOR,
        "button[type='submit'], input[type='submit']"
    )

    if submit_buttons:
        driver.execute_script("arguments[0].click();", submit_buttons[0])
    else:
        driver.find_element(By.TAG_NAME, "form").submit()

    wait_page_ready(driver)

    if not wait_for_supervisor_request(group, cosupervisor):
        errors = collect_page_errors(driver)

        raise AssertionError(
            "Co-supervisor request was not created.\n"
            f"URL: {driver.current_url}\n"
            f"Errors:\n{errors or 'No visible error found'}\n"
            f"Preview: {driver.page_source[:1200].lower()}"
        )

    assert wait_for_notification(cosupervisor), "Co-supervisor notification was not created"

    driver.get(f"{BASE_URL}/accounts/logout/")
    login(driver, "SeleniumCoSupervisor", COSUPERVISOR_PASSWORD)

    driver.get(f"{BASE_URL}/research/supervisor-requests/")
    wait_page_ready(driver)

    page_text = driver.page_source.lower()

    assert "selenium cosupervisor group" in page_text, "Co-supervisor request not visible to teacher"
    assert "co-supervisor" in page_text or "co_supervisor" in page_text, "Request type not shown as co-supervisor"

    print("Co-Supervisor Request Notification Test Passed ✅")

finally:
    driver.quit()

