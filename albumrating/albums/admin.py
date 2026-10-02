from django.contrib import admin
from .models import Album, Review

class AlbumAdmin(admin.ModelAdmin):
    ordering = ['name']
    search_fields = ['name']
admin.site.register(Album, AlbumAdmin)
admin.site.register(Review)
# Register your models here.
