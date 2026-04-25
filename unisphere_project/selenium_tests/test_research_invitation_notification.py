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
from research.models import ResearchGroup, ResearchGroupInvitation
from notifications.models import Notification

PASSWORD = "TestPass123@#"

leader = ensure_user(
    username="selenium_research_inviter",
    password=PASSWORD,
    role="student",
    email="selenium_research_inviter@uap-bd.edu",
    first_name="Research",
    last_name="Leader",
)

invitee = ensure_user(
    username="selenium_research_invitee",
    password=PASSWORD,
    role="student",
    email="selenium_research_invitee@uap-bd.edu",
    first_name="Research",
    last_name="Invitee",
)

ResearchGroup.objects.filter(name="Selenium Closed Invitation Group").delete()

group = ResearchGroup.objects.create(
    name="Selenium Closed Invitation Group",
    description="Closed group for invitation notification test.",
    research_area="Artificial Intelligence",
    group_type="closed",
    created_by=leader,
    status="forming",
)
group.members.add(leader)

ResearchGroupInvitation.objects.filter(group=group, invited_user=invitee).delete()
Notification.objects.filter(recipient=invitee, title="Research Group Invitation").delete()

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    login(driver, "selenium_research_inviter", PASSWORD)

    driver.get(f"{BASE_URL}/research/groups/{group.pk}/")
    wait_page_ready(driver)

    Select(wait.until(EC.presence_of_element_located((By.NAME, "invited_user")))).select_by_value(str(invitee.pk))
    driver.find_element(By.XPATH, "//form[contains(@action, 'send-invitation')]").submit()
    wait_page_ready(driver)

    assert ResearchGroupInvitation.objects.filter(
        group=group,
        invited_user=invitee,
        status="pending"
    ).exists(), "Research group invitation was not created"

    assert Notification.objects.filter(
        recipient=invitee,
        title="Research Group Invitation",
        link=f"/research/groups/{group.pk}/"
    ).exists(), "Invitation notification was not created"

    driver.get(f"{BASE_URL}/accounts/logout/")
    login(driver, "selenium_research_invitee", PASSWORD)

    driver.get(f"{BASE_URL}/notifications/")
    wait_page_ready(driver)

    page_text = driver.page_source.lower()
    assert "research group invitation" in page_text, "Invitation notification not visible to invited user"

    print("Research Invitation Notification Test Passed ✅")

finally:
    driver.quit()
