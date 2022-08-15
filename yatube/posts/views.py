from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow


COUNT_POST = 10


def page(request, post_list):
    paginator = Paginator(post_list, COUNT_POST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    posts = Post.objects.select_related('group').all()[:COUNT_POST]
    post_list = Post.objects.all()
    page_obj = page(request, post_list)
    context = {
        'posts': posts,
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()[:COUNT_POST]
    post_list = group.posts.all()
    page_obj = page(request, post_list)
    title = ''
    context = {
        'title': title,
        'group': group,
        'posts': posts,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    page_obj = page(request, post_list)
    context = {
        'author': author,
        'num_post_list': post_list.count(),
        'page_obj': page_obj,
        'following': False,
    }
    if request.user.is_authenticated:
        if Follow.objects.filter(user=request.user, author=author).exists():
            context['following'] = True
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    posts = Post.objects.filter(author__exact=post.author).count()
    posts_count = posts
    form = CommentForm()
    comments = post.comments.all().select_related('author')
    context = {
        'post': post,
        'posts_count': posts_count,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required(login_url="user:login")
def post_create(request):
    form = PostForm()
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', username=request.user.username)
        context = {'form': form}
    context = {'form': form}
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'post': post,
        'is_edit': True,
    }
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.id)
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = page(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(
            user=request.user,
            author=author
        )
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:follow_index')
