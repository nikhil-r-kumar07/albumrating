from django.contrib import admin
from .models import Profile, AlbumList, ListItem, QueueItem, Favorite, DiaryEntry, Follow, Notification

class ListItemInline(admin.TabularInline):
    model = ListItem
    extra = 0

class AlbumListAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'updated']
    inlines = [ListItemInline]

admin.site.register(Profile)
admin.site.register(AlbumList, AlbumListAdmin)
admin.site.register(QueueItem)
admin.site.register(Favorite)
admin.site.register(DiaryEntry)
admin.site.register(Follow)
admin.site.register(Notification)
