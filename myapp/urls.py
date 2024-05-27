from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required

urlpatterns = [
    # Your other URL patterns
    path('register/', views.user_register, name='user_register'),
    path('', views.user_login, name='user_login'),
    path('dashboard/', login_required(views.dashboard), name='dashboard'),  # Add this line
    path('update_profile/', login_required(views.update_profile), name='update_profile'),
    path('change_password/', login_required(views.change_password), name='change_password'),
    path('view_profile/', views.view_profile, name='view_profile'),
    path('logout/', views.logout_view, name='logout'),
    path('add-comment/<int:post_id>/', views.add_comment, name='add_comment'),
    path('view-comments/<int:post_id>/', views.view_comments, name='view_comments'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
