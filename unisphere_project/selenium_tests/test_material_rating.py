import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "unilink.settings")

import django
django.setup()

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from materials.models import StudyMaterial, MaterialRating

from common import get_driver, login, BASE_URL

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


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
    user.email = f"{username}@uap-bd.edu"
    user.department = "CSE"
    user.university_id = f"U{abs(hash(username)) % 1000000:06d}"
    user.set_password(PASSWORD)
    user.save()

    return user


def print_material_rating_debug(driver, material, student):
    print("\n========== MATERIAL RATING DEBUG ==========")
    print("Current URL:", driver.current_url)
    print("Page Title:", driver.title)
    print("Material ID:", material.pk)
    print("Student:", student.username)

    ratings = MaterialRating.objects.filter(material=material, user=student)

    print("Rating exists:", ratings.exists())

    for rating in ratings:
        print("Saved Score:", rating.score)
        if hasattr(rating, "review"):
            print("Saved Review:", rating.review)

    print("\nForms Found:", len(driver.find_elements(By.TAG_NAME, "form")))

    forms = driver.find_elements(By.TAG_NAME, "form")
    for index, form in enumerate(forms, start=1):
        print(f"\n--- FORM {index} ---")
        print(form.get_attribute("outerHTML")[:1500])

    print("\nPage Text:")
    print(driver.find_element(By.TAG_NAME, "body").text[:3000])
    print("===========================================\n")


def get_or_create_material(teacher):
    material = StudyMaterial.objects.filter(
        title="Selenium Rating Test Material"
    ).first()

    if material:
        material.is_approved = True
        material.uploaded_by = teacher
        material.save()
        return material

    test_file = SimpleUploadedFile(
        "rating_test.pdf",
        b"%PDF-1.4 selenium rating test",
        content_type="application/pdf"
    )

    material = StudyMaterial.objects.create(
        title="Selenium Rating Test Material",
        description="Material for rating test",
        course_name="CSE 314",
        semester="3.1",
        topic="Software Engineering",
        tags="testing, selenium",
        file=test_file,
        uploaded_by=teacher,
        is_approved=True,
    )

    return material


def find_rating_form(driver):
    forms = driver.find_elements(By.TAG_NAME, "form")

    if not forms:
        raise AssertionError("No form found on material detail page")

    for form in forms:
        html = form.get_attribute("innerHTML").lower()
        text = form.text.lower()

        if (
            "score" in html
            or "rating" in html
            or "stars" in html
            or "review" in html
            or "rate" in text
            or "rating" in text
        ):
            return form

    return forms[-1]


def set_rating_score(driver, form, score="5"):


    possible_names = ["score", "rating", "stars"]


    for name in possible_names:
        elements = form.find_elements(By.NAME, name)

        for element in elements:
            if element.tag_name.lower() == "select":
                Select(element).select_by_value(score)
                return


    for name in possible_names:
        selector = f"input[name='{name}'][value='{score}']"
        elements = form.find_elements(By.CSS_SELECTOR, selector)

        if elements:
            rating_input = elements[0]

            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});",
                rating_input
            )

            driver.execute_script(
                """
                arguments[0].click();
                arguments[0].checked = true;
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                """,
                rating_input
            )
            return


    for name in possible_names:
        elements = form.find_elements(By.NAME, name)

        if elements:
            rating_input = elements[0]

            driver.execute_script(
                """
                arguments[0].value = arguments[1];
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                """,
                rating_input,
                score
            )
            return

    raise AssertionError("Could not find rating score field")


def fill_review_if_exists(form):
    possible_review_names = ["review", "comment", "feedback"]

    for name in possible_review_names:
        fields = form.find_elements(By.NAME, name)

        if fields:
            field = fields[0]
            field.clear()
            field.send_keys("Excellent material, very helpful for exam preparation.")
            return


def submit_rating_form(driver, form):
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});",
        form
    )

    driver.execute_script(
        "arguments[0].requestSubmit();",
        form
    )


def wait_until_rating_saved(driver, material, student):
    try:
        WebDriverWait(driver, 10).until(
            lambda d: MaterialRating.objects.filter(
                material=material,
                user=student,
                score=5
            ).exists()
        )
    except TimeoutException:
        print_material_rating_debug(driver, material, student)
        raise AssertionError("Material rating was not saved in database")



teacher = ensure_user("selenium_mat_teacher", role="teacher")
student = ensure_user("selenium_mat_rater", role="student")


material = get_or_create_material(teacher)


MaterialRating.objects.filter(
    material=material,
    user=student
).delete()


driver = get_driver()

try:

    login(driver, "selenium_mat_rater", PASSWORD)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )


    driver.get(f"{BASE_URL}/materials/{material.pk}/")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    print("Material detail URL:", driver.current_url)


    rating_form = find_rating_form(driver)


    set_rating_score(driver, rating_form, "5")


    fill_review_if_exists(rating_form)

    submit_rating_form(driver, rating_form)


    wait_until_rating_saved(driver, material, student)

    assert MaterialRating.objects.filter(
        material=material,
        user=student,
        score=5
    ).exists(), "Material rating was not saved in database"

    print("Material Rating Test Passed ✅")

finally:
    driver.quit()