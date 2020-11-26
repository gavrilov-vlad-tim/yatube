from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import cache_page

from .models import Comment, Follow, Group, Post, User
from .forms import CommentForm, PostForm


def index (request):
    posts = Post.objects.order_by('-pub_date')
    posts = Paginator(posts, 10)
    page_number = request.GET.get('page', 1)
    page = posts.get_page(page_number) 
    return render(request, 'index.html', {'paginator': posts, 'page': page, 'index': True} )


@login_required
def follow_index(request):
    user = request.user
    follow = Follow.objects.filter(user=user).values('author')
    posts = Post.objects.filter(author__in=follow).order_by('-pub_date')
    posts = Paginator(posts, 10)
    page_number = request.GET.get('page', 1)
    page = posts.get_page(page_number)
    return render(request, 'follow.html', {'paginator': posts, 'page': page, 'follow': True})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group).order_by('-pub_date')
    posts = Paginator(posts, 10)
    page_number = request.GET.get('page', 1)
    page = posts.get_page(page_number)
    return render(request, 'group.html', {'group': group, 'paginator': posts, 'page': page})


@login_required
def new_post(request):
    if request.method == 'POST':        
        form = PostForm(request.POST, files=request.FILES or None)

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('index')
        
        return render(request, 'new_post.html', {'form': form})
    
    form = PostForm()
    return render(request, 'new_post.html', {'form': form})


def profile(request, username):

    profile = get_object_or_404(User, username=username)
    user_is_author = False
    following = False

    if  request.user.is_authenticated:
        user = request.user
        user_is_author = (user != profile)
        following = Follow.objects.filter(user=user, author=profile).exists()

    posts = Post.objects.filter(author=profile).order_by('-pub_date')
    posts = Paginator(posts, 10)
    page_number = request.GET.get('page', 1)
    page = posts.get_page(page_number)
    return render(
        request, 'profile.html',  
        {
        'following': following,
        'paginator': posts, 
        'page': page, 'profile': profile,
        'user_is_author': user_is_author
        }
    )


@login_required
def profile_follow(request, username):
    user = request.user
    following_author = get_object_or_404(User, username=username)

    if user == following_author:
        return redirect('profile', username=username)
    
    try:
        Follow.objects.get(user=user, author=following_author)
    except Follow.DoesNotExist:    
        Follow.objects.create(user=user, author=following_author)

    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    following_author = get_object_or_404(User, username=username)

    if user == following_author:
        return redirect('profile', username=username)
    
    follow = get_object_or_404(Follow, user=user, author=following_author)
    follow.delete()

    return redirect('profile', username=username)

def post_view(request, username, post_id):
    profile = User.objects.get(username=username)
    posts_count = Post.objects.filter(author=profile).count()
    post = Post.objects.get(pk=post_id)
    form = CommentForm()
    comments = Comment.objects.filter(post=post)
    return render(
        request, 
        'post.html', 
        {
        'post': post, 'form': form,
        'posts_count': posts_count, 
        'profile': profile,  
        'comments': comments
        }
    )


@login_required
def post_edit(request, username, post_id):
    post = Post.objects.get(pk=post_id)
    if not request.user.is_authenticated:
        return redirect('post_view', username=username, post_id=post.pk)
    
    profile = User.objects.get(username=request.user)
    author = post.author
    if profile != author:
        return redirect('post_view', username=username, post_id=post.pk)

    if request.method == 'POST':        
        form = PostForm(request.POST, files=request.FILES or None, instance=post)

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.pub_date = timezone.now()
            post.save()
            return redirect('post_view', username=username, post_id=post.pk)
    
        return render(request, 'new_post.html', {'form': form, 'post': post})

    form = PostForm(instance=post)
    return render(request, 'new_post.html', {'form': form, 'post': post})


@login_required
def add_comment(request, username, post_id):
    comment_author = request.user
    related_post = get_object_or_404(Post, pk=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)

        if form.is_valid:
            comment = form.save(commit=False)
            comment.post = related_post
            comment.author = comment_author
            comment.save()
            return redirect('post_view', related_post.author.username, related_post.pk)
        return render(request, 'post.html', {'form': form, 'post': related_post})
    return redirect('post_view', username=username, post_id=post_id)


def page_not_found(request, exception):
    return render(request, 'misc/404.html', status=404)


def server_error(request):
    return render(request, 'misc/500.html', status=500)