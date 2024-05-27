from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from .models import Profile, Post, Comments
from .forms import ProfileForm, CommentForm

def user_register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')   
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required
def dashboard(request):
    posts = Post.objects.all()
    return render(request, 'dashboard.html', {'posts': posts})

@login_required
def update_profile(request):
    user = request.user
    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        profile = Profile(user=user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'update_profile.html', {'form': form})

@login_required
def view_profile(request):
    user_profile = Profile.objects.get(user=request.user)
    return render(request, 'view_profile.html', {'user_profile': user_profile})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('user_login')

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.post = post
            comment.save()
            return redirect('dashboard')
    else:
        form = CommentForm()
    return render(request, 'add_comment.html', {'form': form, 'post': post})

from nltk.corpus import sentiwordnet as swn
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet

def calculate_sentiment(comment_text):
    lemmatizer = WordNetLemmatizer()
    tokens = word_tokenize(comment_text)
    pos_score = 0
    neg_score = 0
    token_count = 0

    for token in tokens:
        lemma = lemmatizer.lemmatize(token)
        synsets = wordnet.synsets(lemma)
        if not synsets:
            continue
        synset = synsets[0]
        swn_synset = swn.senti_synset(synset.name())
        pos_score += swn_synset.pos_score()
        neg_score += swn_synset.neg_score()
        token_count += 1

    if token_count == 0:
        return 0, 'neutral'
    
    avg_pos_score = pos_score / token_count
    avg_neg_score = neg_score / token_count

    if avg_pos_score > avg_neg_score:
        sentiment_label = 'positive'
        sentiment_score = avg_pos_score
    elif avg_neg_score > avg_pos_score:
        sentiment_label = 'negative'
        sentiment_score = avg_neg_score
    else:
        sentiment_label = 'neutral'
        sentiment_score = 0
    
    return sentiment_score, sentiment_label

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    existing_comment = Comments.objects.filter(user=request.user, post=post).first()
    
    if existing_comment:
        return render(request, 'add_comment.html', {'post': post, 'existing_comment': existing_comment})
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.post = post
            sentiment_score, sentiment_label = calculate_sentiment(comment.comment_text)
            comment.sentiment_score = sentiment_score
            comment.sentiment_label = sentiment_label
            comment.save()
            return redirect('dashboard')
    else:
        form = CommentForm()
    
    return render(request, 'add_comment.html', {'form': form, 'post': post})


@login_required
def view_comments(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = Comments.objects.filter(post=post)
    return render(request, 'view_comments.html', {'post': post, 'comments': comments})
