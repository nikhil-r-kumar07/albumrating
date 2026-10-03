from django.contrib import admin
from .models import Profile, AlbumList, ListItem, QueueItem

class ListItemInline(admin.TabularInline):
    model = ListItem
    extra = 0

class AlbumListAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'updated']
    inlines = [ListItemInline]

admin.site.register(Profile)
admin.site.register(AlbumList, AlbumListAdmin)
admin.site.register(QueueItem)
