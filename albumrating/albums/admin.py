from django.contrib import admin
from .models import Album, Review, Artist

class AlbumAdmin(admin.ModelAdmin):
    ordering = ['name']
    search_fields = ['name']
admin.site.register(Album, AlbumAdmin)
admin.site.register(Review)
admin.site.register(Artist)

