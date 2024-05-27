from django.contrib.auth.models import User
from django.db import models
from django.core import validators

from django.db import models
from django.contrib.auth.models import User
from django.core import validators

from django.db import models
from django.contrib.auth.models import User
from django.core import validators

class Profile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, default="")
    email = models.EmailField(default="")
    date_of_birth = models.DateField(default=None, blank=True, null=True)
    age = models.IntegerField(default=None, blank=True, null=True, validators=[validators.MinValueValidator(0)])
    phone_number = models.CharField(
        max_length=20,
        default="",
        blank=True,
        null=True,
        validators=[validators.RegexValidator(regex='^[0-9]*$', message='Enter a valid phone number.', code='invalid_number')]
    )  # Only allow numeric values
    address = models.TextField(default="", blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', default='default.jpg')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    
    def __str__(self):
        return self.user.username



class Post(models.Model):
    topic = models.CharField(max_length=255)
    post_date = models.DateTimeField(auto_now_add=True)
    post_picture = models.ImageField(upload_to='post_pictures/', blank=True, null=True)
    post_content = models.TextField(default='New Post')

    def __str__(self):
        return self.topic

class Comments(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    comment_text = models.TextField()
    comment_date = models.DateTimeField(auto_now_add=True)
    sentiment_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    sentiment_label = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"Comment by {self.user.username} on '{self.post.topic}'"

