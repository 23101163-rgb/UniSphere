from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Category, Thread, Reply, Vote
from .forms import ThreadForm, ReplyForm
from notifications.utils import create_notification

@login_required
def forum_home(request):
    categories = Category.objects.all()
    recent_threads = Thread.objects.filter(is_flagged=False)[:20]
    form = ThreadForm()

    if request.method == 'POST':
        form = ThreadForm(request.POST, request.FILES)
        if form.is_valid():
            t = form.save(commit=False)
            t.author = request.user
            t.save()
            messages.success(request, 'Post published!')
            return redirect('forum:home')

    return render(request, 'forum/forum_home.html', {
        'categories': categories,
        'recent_threads': recent_threads,
        'form': form,
    })

@login_required
def category_threads(request, slug):
    category = get_object_or_404(Category, slug=slug)
    threads = category.threads.filter(is_flagged=False)
    return render(request, 'forum/category_threads.html', {'category': category, 'threads': threads})

@login_required
def thread_detail(request, pk):
    thread = get_object_or_404(Thread, pk=pk)
    thread.views_count += 1
    thread.save(update_fields=['views_count'])
    comments = thread.replies.filter(is_flagged=False, parent=None)
    if request.method == 'POST':
        form = ReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.thread = thread
            reply.author = request.user
            parent_id = request.POST.get('parent_id')
            if parent_id:
                reply.parent = get_object_or_404(Reply, pk=parent_id)
            reply.save()

            # ✅ Notification: reply to comment
            if reply.parent and reply.parent.author != request.user:
                create_notification(
                    recipient=reply.parent.author,
                    title='New Reply on Your Comment',
                    message=f'{request.user.get_full_name()} replied to your comment on "{thread.title}".',
                    link=f'/forum/thread/{thread.pk}/'
                )
            # ✅ Notification: comment on post
            elif thread.author != request.user:
                create_notification(
                    recipient=thread.author,
                    title='New Comment on Your Post',
                    message=f'{request.user.get_full_name()} commented on your post "{thread.title}".',
                    link=f'/forum/thread/{thread.pk}/'
                )

            messages.success(request, 'Comment posted!')
            return redirect('forum:thread_detail', pk=pk)
    else:
        form = ReplyForm()
    return render(request, 'forum/thread_detail.html', {'thread': thread, 'comments': comments, 'form': form})

@login_required
def thread_create(request):
    if request.method == 'POST':
        form = ThreadForm(request.POST, request.FILES)
        if form.is_valid():
            t = form.save(commit=False)
            t.author = request.user
            t.save()
            messages.success(request, 'Post published!')
            return redirect('forum:thread_detail', pk=t.pk)
    else:
        form = ThreadForm()
    return render(request, 'forum/thread_form.html', {'form': form, 'title': 'Create New Post'})

@login_required
def thread_edit(request, pk):
    thread = get_object_or_404(Thread, pk=pk)

    # Only author can edit
    if thread.author != request.user:
        messages.error(request, 'You can only edit your own posts.')
        return redirect('forum:thread_detail', pk=pk)

    if request.method == 'POST':
        form = ThreadForm(request.POST, request.FILES, instance=thread)
        if form.is_valid():
            form.save()
            messages.success(request, 'Post updated!')
            return redirect('forum:thread_detail', pk=pk)
    else:
        form = ThreadForm(instance=thread)

    return render(request, 'forum/thread_form.html', {'form': form, 'title': 'Edit Post'})

@login_required
def thread_delete(request, pk):
    thread = get_object_or_404(Thread, pk=pk)

    # Only author or admin can delete
    if thread.author != request.user and not request.user.is_admin_user():
        messages.error(request, 'You can only delete your own posts.')
        return redirect('forum:thread_detail', pk=pk)

    if request.method == 'POST':
        thread.delete()
        messages.success(request, 'Post deleted.')
        return redirect('forum:home')

    return render(request, 'forum/thread_confirm_delete.html', {'thread': thread})

@login_required
def upvote_thread(request, pk):
    thread = get_object_or_404(Thread, pk=pk)
    vote, created = Vote.objects.get_or_create(user=request.user, thread=thread, defaults={'vote_type': 'up'})
    if not created:
        vote.delete()
    else:
        if thread.author != request.user:
            create_notification(
                recipient=thread.author,
                title='Someone Liked Your Post',
                message=f'{request.user.get_full_name()} liked your post "{thread.title}".',
                link=f'/forum/thread/{thread.pk}/'
            )
    next_url = request.GET.get('next', '')
    if next_url == 'feed':
        return redirect('forum:home')
    return redirect('forum:thread_detail', pk=pk)

@login_required
def upvote_reply(request, pk):
    reply = get_object_or_404(Reply, pk=pk)
    vote, created = Vote.objects.get_or_create(user=request.user, reply=reply, defaults={'vote_type': 'up'})
    if not created:
        vote.delete()
    else:
        if reply.author != request.user:
            create_notification(
                recipient=reply.author,
                title='Someone Liked Your Comment',
                message=f'{request.user.get_full_name()} liked your comment on "{reply.thread.title}".',
                link=f'/forum/thread/{reply.thread.pk}/'
            )
    return redirect('forum:thread_detail', pk=reply.thread.pk)

@login_required
def flag_content(request, content_type, pk):
    if content_type == 'thread':
        obj = get_object_or_404(Thread, pk=pk)
    else:
        obj = get_object_or_404(Reply, pk=pk)
    obj.is_flagged = True
    obj.save()
    messages.info(request, 'Content flagged for review.')
    return redirect(request.META.get('HTTP_REFERER', 'forum:home'))

@login_required
def search_threads(request):
    query = request.GET.get('q', '')
    threads = Thread.objects.filter(Q(title__icontains=query) | Q(content__icontains=query)) if query else Thread.objects.none()
    return render(request, 'forum/search_results.html', {'threads': threads, 'query': query})