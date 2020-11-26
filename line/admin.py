from django.contrib import admin
from .models import User, Keyword

# Register your models here.
class KeywordInline(admin.TabularInline):
    model = Keyword.user_id.through

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'follow_date', 'status')
    inlines = [KeywordInline]

@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'create_time')

