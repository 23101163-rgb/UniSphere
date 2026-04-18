from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, F
from notifications.utils import create_notification
from .models import StudyMaterial, MaterialRating
from .forms import StudyMaterialForm, MaterialRatingForm


@login_required
def material_list(request):
    materials = StudyMaterial.objects.filter(is_approved=True)

    query = request.GET.get('q', '').strip()
    semester = request.GET.get('semester', '').strip()
    course = request.GET.get('course', '').strip()

    if query:
        materials = materials.filter(
            Q(title__icontains=query) |
            Q(tags__icontains=query) |
            Q(topic__icontains=query) |
            Q(course_name__icontains=query)
        )

    if semester:
        materials = materials.filter(semester=semester)

    if course:
        materials = materials.filter(course_name__icontains=course)

    return render(request, 'materials/material_list.html', {
        'materials': materials,
        'query': query,
        'semester': semester,
        'course': course,
        'semesters': StudyMaterial.SEMESTER_CHOICES,
    })


@login_required
def material_detail(request, pk):
    material = get_object_or_404(StudyMaterial, pk=pk)

    if not material.is_approved and material.uploaded_by != request.user and not request.user.is_admin_user():
        messages.error(request, 'This material is not approved yet.')
        return redirect('materials:semesters')

    user_rating = MaterialRating.objects.filter(material=material, user=request.user).first()

    if request.method == 'POST':
        form = MaterialRatingForm(request.POST, instance=user_rating)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.material = material
            rating.user = request.user
            rating.save()
            messages.success(request, 'Rating submitted successfully.')
            return redirect('materials:detail', pk=pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MaterialRatingForm(instance=user_rating)

    return render(request, 'materials/material_detail.html', {
        'material': material,
        'form': form,
        'user_rating': user_rating,
    })


@login_required
def material_create(request):
    if request.method == 'POST':
        form = StudyMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.uploaded_by = request.user
            material.is_approved = (
                    request.user.is_teacher() or
                    request.user.is_alumni() or
                    request.user.is_admin_user()
            )
            material.save()


            create_notification(
                user=request.user,
                title="Material Uploaded",
                message=f'Your material "{material.title}" has been uploaded successfully',
                link=f'/materials/{material.pk}/'
            )

            if material.is_approved:
                messages.success(request, 'Material uploaded successfully.')
            else:
                messages.success(request, 'Material uploaded successfully and is awaiting approval.')

            return redirect('materials:semesters')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudyMaterialForm()

    return render(request, 'materials/material_form.html', {
        'form': form,
        'title': 'Upload Study Material'
    })


@login_required
def material_edit(request, pk):
    material = get_object_or_404(StudyMaterial, pk=pk)

    if material.uploaded_by != request.user and not request.user.is_admin_user():
        messages.error(request, 'Permission denied.')
        return redirect('materials:semesters')

    if request.method == 'POST':
        form = StudyMaterialForm(request.POST, request.FILES, instance=material)
        if form.is_valid():
            updated_material = form.save(commit=False)

            if not request.user.is_admin_user() and not request.user.is_teacher():
                updated_material.is_approved = False

            updated_material.save()
            messages.success(request, 'Material updated successfully.')
            return redirect('materials:detail', pk=pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudyMaterialForm(instance=material)

    return render(request, 'materials/material_form.html', {
        'form': form,
        'title': 'Edit Material'
    })


@login_required
def material_delete(request, pk):
    material = get_object_or_404(StudyMaterial, pk=pk)

    if material.uploaded_by != request.user and not request.user.is_admin_user():
        messages.error(request, 'Permission denied.')
        return redirect('materials:semesters')

    if request.method == 'POST':
        material.delete()
        messages.success(request, 'Material deleted successfully.')
        return redirect('materials:semesters')

    return render(request, 'materials/material_confirm_delete.html', {
        'material': material
    })


@login_required
def material_download(request, pk):
    material = get_object_or_404(StudyMaterial, pk=pk)

    if not material.is_approved and material.uploaded_by != request.user and not request.user.is_admin_user():
        messages.error(request, 'This material is not approved yet.')
        return redirect('materials:semesters')

    StudyMaterial.objects.filter(pk=material.pk).update(download_count=F('download_count') + 1)


    create_notification(
        user=request.user,
        title="Material Downloaded",
        message=f'You downloaded "{material.title}"',
        link=f'/materials/{material.pk}/'
    )

    # 🔥 2. UPLOADER NOTIFICATION
    if request.user != material.uploaded_by:
        create_notification(
            user=material.uploaded_by,
            title="Material Downloaded",
            message=f'{request.user.get_full_name() or request.user.username} downloaded your material "{material.title}"',
            link=f'/materials/{material.pk}/'
        )

    from django.http import FileResponse
    return FileResponse(
        material.file.open(),
        as_attachment=True,
        filename=material.file.name.split('/')[-1]
    )


@login_required
def material_approve(request, pk):
    if not (request.user.is_teacher() or request.user.is_admin_user()):
        messages.error(request, 'Access denied.')
        return redirect('materials:semesters')

    material = get_object_or_404(StudyMaterial, pk=pk)
    material.is_approved = True
    material.save()

    # 🔔 Notification trigger
    if material.uploaded_by != request.user:
        create_notification(
            recipient=material.uploaded_by,
            title='Material Approved',
            message=f'Your material "{material.title}" has been approved and is now available.',
            link=f'/materials/{material.pk}/'
        )

    messages.success(request, f'"{material.title}" approved successfully.')
    return redirect('materials:pending')
@login_required
def material_pending(request):
    if not (request.user.is_teacher() or request.user.is_admin_user()):
        messages.error(request, 'Access denied.')
        return redirect('materials:semesters')

    materials = StudyMaterial.objects.filter(is_approved=False)
    return render(request, 'materials/material_pending.html', {
        'materials': materials
    })
@login_required
def material_semesters(request):
    semester_values = ['1.1', '1.2', '2.1', '2.2', '3.1', '3.2', '4.1', '4.2']
    semester_data = []

    for sem in semester_values:
        semester_materials = StudyMaterial.objects.filter(is_approved=True, semester=sem)

        resource_count = semester_materials.count()
        course_count = semester_materials.values('course_name').distinct().count()

        semester_data.append({
            'value': sem,
            'label': f'Semester {sem}',
            'count': resource_count,
            'course_count': course_count,
        })

    return render(request, 'materials/material_semesters.html', {
        'semester_data': semester_data
    })
@login_required
def material_courses_by_semester(request, semester):
    materials = StudyMaterial.objects.filter(is_approved=True, semester=semester)


    from django.db.models import Count
    courses = (
        materials
        .values('course_name')
        .annotate(total=Count('id'))
        .order_by('course_name')
    )
    if not courses:
        messages.info(request, "No courses found for this semester.")

    semester_label = f"Semester {semester}"

    return render(request, 'materials/material_courses.html', {
        'semester': semester,
        'semester_label': semester_label,
        'courses': courses,
    })
@login_required
def materials_by_course(request, semester, course_name):
    materials = StudyMaterial.objects.filter(
        is_approved=True,
        semester=semester,
        course_name=course_name
    ).select_related('uploaded_by').order_by('-created_at')
    query = request.GET.get('q', '').strip()
    if query:
        materials = materials.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query)
        )

    total_materials = materials.count()

    semester_label = f"Semester {semester}"

    return render(request, 'materials/material_course_resources.html', {
        'materials': materials,
        'semester': semester,
        'semester_label': semester_label,
        'course_name': course_name,
        'total_materials': total_materials,
    })