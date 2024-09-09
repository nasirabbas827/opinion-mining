from django.contrib import admin
from .models import Profile, Post, Comments

class CommentsAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'comment_text', 'comment_date', 'sentiment_score', 'sentiment_label')
    readonly_fields = ('user', 'post', 'comment_text', 'comment_date', 'sentiment_score', 'sentiment_label')

    def has_add_permission(self, request):
        # Prevent admins from adding new comments
        return False

    def has_change_permission(self, request, obj=None):
        # Prevent admins from editing comments
        return False

# Register models
admin.site.register(Profile)
admin.site.register(Post)
admin.site.register(Comments, CommentsAdmin)
