from django.http import HttpResponse
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
@login_required
def dashboard(request):
    posts = Post.objects.all()
    
    # Calculate average sentiment score for each post
    for post in posts:
        comments = Comments.objects.filter(post=post)
        if comments:
            total_score = sum(comment.sentiment_score or 0 for comment in comments)
            avg_score = total_score / comments.count()
            post.avg_sentiment_score = avg_score
        else:
            post.avg_sentiment_score = 0
        
        # Determine the sentiment label
        if post.avg_sentiment_score > 0.01:
            post.sentiment_label = 'Good'
        elif post.avg_sentiment_score < -0.1:
            post.sentiment_label = 'Bad'
        else:
            post.sentiment_label = 'Worst'
    
    # Sort posts by their average sentiment score
    posts = sorted(posts, key=lambda x: x.avg_sentiment_score, reverse=True)
    
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
    try:
        user_profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        return HttpResponse("Profile does not exist. Please create a profile first.", status=404)

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
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk import pos_tag

# Map NLTK POS tags to WordNet POS tags
def get_wordnet_pos(treebank_tag):
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return None

def calculate_sentiment(comment_text):
    lemmatizer = WordNetLemmatizer()
    tokens = word_tokenize(comment_text)
    pos_tags = pos_tag(tokens)  # Get POS tags for tokens

    pos_score = 0
    neg_score = 0
    token_count = 0
    negation = False  # To handle negation

    for token, pos in pos_tags:
        wordnet_pos = get_wordnet_pos(pos) or wordnet.NOUN  # Default to NOUN if no POS match
        lemma = lemmatizer.lemmatize(token, pos=wordnet_pos)
        synsets = wordnet.synsets(lemma, pos=wordnet_pos)
        
        if not synsets:
            continue

        swn_scores = []
        for synset in synsets:
            try:
                swn_synset = swn.senti_synset(synset.name())
                swn_scores.append((swn_synset.pos_score(), swn_synset.neg_score()))
            except:
                continue

        if not swn_scores:
            continue

        avg_pos = sum([s[0] for s in swn_scores]) / len(swn_scores)
        avg_neg = sum([s[1] for s in swn_scores]) / len(swn_scores)

        if token.lower() in ['not', "n't"]:  # Handle negation
            negation = True
            continue

        if negation:
            pos_score += avg_neg  # Reverse the sentiment
            neg_score += avg_pos
            negation = False
        else:
            pos_score += avg_pos
            neg_score += avg_neg

        token_count += 1

    if token_count == 0:
        return 0, 'neutral'

    avg_pos_score = pos_score / token_count
    avg_neg_score = neg_score / token_count

    # Adjust classification logic with thresholds
    if avg_pos_score > avg_neg_score and avg_pos_score > 0.05:  # Consider positive if score > 0.05
        sentiment_label = 'positive'
        sentiment_score = avg_pos_score
    elif avg_neg_score > avg_pos_score and avg_neg_score > 0.05:  # Consider negative if score > 0.05
        sentiment_label = 'negative'
        sentiment_score = -avg_neg_score  # Negative score for negative sentiment
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
            comment.sentiment_score = sentiment_score  # Now handles both positive and negative scores
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
